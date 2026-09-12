# 长 md 文件

**目录**：

- [一、实验要求](#1)
- [二、辨识代码说明](#2)
  - [1. 步长 `step` 的选取](#21)
  - [2. 数据截断](#22)
  - [3. 最小二乘估计与特征根、极点、$\omega_n, \zeta$ 的计算](#23)
  - [4. 对辨识等效电阻的线性拟合](#24)
  - [5. 辨识电感 $L$ 和辨识电容 $C$ 的计算](#25)
  - [6. 发散数据处理](#26)
- [三、数据处理结果](#3)
  - [1. 各组数据 $U-t$ 图](#31)
  - [2. 电阻 $R$ 的线性拟合](#32)
- [四、结果分析](#4)
- [五、完整代码](#5)

## .实验要求 {#1}

1. 将电阻调至最小，对试验装置进行阶跃测试，通过示波器观察系统响应并记录数据，在 MATLAB 中编程实现最小二乘辨识，计算系统**特征根、阻尼比、自然角频率**。

2. 调节滑动变阻器（通过万用表测量滑动变阻器阻值），重复进行 4 组阶跃测试，观察系统从欠阻尼向过阻尼状态转变，在 MATLAB 中编程实现最小二乘辨识，结合试验结果分析系统特征根、阻尼比、自然角频率**变化规律**。

3. 利用上述试验结果，估计每组试验状态下的**等效电阻、电感、电容**，**与器件标称值**_（电感 $1 \mathrm{mH}$，电容 $330 \mathrm{nF}$，电位器范围 $0 \sim 100 \mathrm{\Omega}$）_**进行对比**讨论。

## .辨识代码说明 {#2}

本报告使用 MATLAB 代码编程，这里取几个重要部分进行说明。

### .步长 `step` 的选取 {#21}

为模拟不同采样间隔，数据处理在同一组高速率采集数据的基础上，调节下采样间隔点数 `step`（每多少个数据点取一个）。

### .数据截断 {#22}

可只截取开关闭合后的一段数据点进行分析，此时输入（开关状态）恒为 $u(k) = 1$。此时建模过程可忽略 $u(k)$，因为对一般的系统辨识，离散差分模型为：

$$
y(k) + a_{n-1}y(k-1) + \cdots + a_0y(k-n) = b_n u(k) + b_{n-1} u(k-1) + \cdots + b_0 u(k-n)
$$

若 $u(k)$ 恒为 1，则：

$$
y(k) + a_{n-1}y(k-1) + \cdots + a_0y(k-n) = b_n + b_{n-1} + \cdots + b_0
$$

右边为定值，故可以直接对 $y$ 作最小二乘拟合。辨识时可忽略 $u(k)$，直接取 $\boldsymbol{x} = [a_1, a_0]^{\mathsf{T}}$ 作为变量。

截取阶跃点及后续震荡段的代码如下：

```matlab
% 智能动态截取：寻找阶跃点并截取后续振荡段
[~, jump_idx] = max(abs(diff(y_raw)));
start_idx = max(1, jump_idx - 20);
end_idx = min(length(y_raw), start_idx + 1200);

y = y_raw(start_idx:end_idx);
t = t_raw(start_idx:end_idx);

% 下采样 (step=50 左右通常能获得最稳定的辨识结果)
y = y(1:step:end);
t = t(1:step:end);
y = y - mean(y(end-20:end)); % 去直流
```

### .最小二乘估计与特征根、极点、$\omega_n, \zeta$ 的计算 {#23}

此处直接上代码：

```matlab
% 最小二乘辨识
Y = y(3:end);
X = [-y(2:end-1), -y(1:end-2)];
theta = pinv(X) * Y;

% 数学法计算极点 (S平面)
Ts = abs(mean(diff(t)));
z_poles = roots([1, theta(1), theta(2)]); % 离散极点
s_poles = log(z_poles) / Ts;              % 连续极点

sigma = -real(s_poles(1));
wd = abs(imag(s_poles(1)));
wn_val = sqrt(sigma^2 + wd^2);
zeta_val = sigma / wn_val;
R_est = 2 * zeta_val * sqrt(1e-3 / 330e-9);
```

**注**：`s_poles` 是连续系统的极点（分母的零点），也就是系统的特征值 $\lambda = a \pm bi$。

### .对辨识等效电阻的线性拟合 {#24}

实测电阻 $R$ 是滑动变阻器的电阻，但电路中还有电感线圈、导线等元件，也会带来一定的电阻。因此，辨识得到的系统等效电阻 $R_{est}$ 一般与实测电阻 $R$ 不等.

一般来说，$R$ 与 $R_{est}$ 差值恒定，即 $R_{est} = R + \Delta R$，而每次的 $\Delta R$ 可能改变。因此可将多组数据的辨识等效电阻进行线性拟合。较好的拟合结果应呈现出近似为 1 的斜率，且决定系数 $R^2$ 接近 1。

拟合过程如下，其中 `R_list` 是实测电阻组成的 List，`R_fit` 是利用实测电阻与拟合方程，计算出的等效电阻的预报值 $\hat{R}_{est}$ 的 List，用来计算拟合的决定系数 $R^2$。

```matlab
p = polyfit(R_list, R_est_list, 1);  % 拟合一阶多项式
k = p(1);
b = p(2);
R_fit = k * R_list + b;
R2 = 1 - sum((R_est_list - R_fit).^2) / sum((R_est_list - mean(R_est_list)).^2);
```

### .辨识电感 $L$ 和辨识电容 $C$ 的计算 {#25}

根据公式：

$$
\omega_n = \frac{1}{\sqrt{LC}}, \qquad \zeta = \frac{R}{2} \sqrt{\frac{C}{L}}
$$

即可计算出辨识电感 $L$ 和辨识电容 $C$。之后再取均值即可。

```matlab
% 计算 L 和 C
L_est = R_est_list ./ (2 .* zeta_list .* wn_list);
C_est = (2 .* zeta_list) ./ (R_est_list .* wn_list);

% 排除第 2 组 (zeta=1 的临界阻尼组，计算会发散，一般建议排除)
idx = [1, 2, 3, 4, 5]; 
L_mean = mean(L_est(idx)) * 1e3; % 转为 mH
C_mean = mean(C_est(idx)) * 1e9; % 转为 nF
```

### .发散数据处理 {#26}

在上一节电感和电容计算中，由于我们的数据有一组极大的 $R = 103.0 \mathrm{\Omega}$，该组接近发散，图如下：

![30%ri|.发散的第 6 组数据](发散.png)

因此我们使用 `idx = [1, 2, 3, 4, 5]` 掩码忽略掉发散的第 6 组，使用前面 5 组计算平均 $L, C$。

## .数据处理结果 {#3}

### .各组数据 $U-t$ 图 {#31}

不同阻值 $R$、不同采样间隔点数 `step` 下，各组数据汇总如下：

![80%ri|.step=50时各组结果](1-各组结果汇总_step=50_converted.png)
![80%ri|.step=30时各组结果](1-各组结果汇总_step=30_converted.png)
![80%ri|.step=10时各组结果](1-各组结果汇总_step=10_converted.png)

三幅图分别对应 `step` = 50, 30, 10。可以看到，随着 `step` 的减小，曲线的大致形状越来越完整（尤其是各组图片左上角 $R = 0.9\mathrm{\Omega}$ 的图片），但细节处出现锯齿状波动。**这可能导致后续辨识出现问题。** 这将在下一部分中体现。

### .电阻 $R$ 的线性拟合 {#32}

**step = 50 时**：

| 组号 | 实测R (Ω) | 特征根 | 阻尼比 ζ | 自然频率 ω_n (rad/s) | 等效电阻 R_est (Ω) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 0.9 | -3461.25 ± 54760.19i | 0.06 | 54869.47 | 6.95 |
| 2 | 14.7 | -10272.55 ± 54715.65i | 0.18 | 55671.61 | 20.32 |
| 3 | 25.0 | -15956.75 ± 51805.99i | 0.29 | 54207.74 | 32.41 |
| 4 | 44.4 | -26818.26 ± 48097.00i | 0.49 | 55068.51 | 53.62 |
| 5 | 69.9 | -37759.77 ± 43938.27i | 0.65 | 57934.20 | 71.76 |
| 6 | 103.0 | -54365.86 ± 0.00i | 1.00 | 54365.86 | 110.10 |

![80%ri|.step=50时线性拟合结果](2-拟合结果_step=50_converted.png)

```text
=== 线性拟合分析 ===
拟合方程: R_est = 0.992 * R + 6.549
决定系数 R² = 0.983563

=== 辨识反推结果 ===
平均辨识电感 L: 0.9915 mH (标称值: 1.0 mH)
平均辨识电容 C: 327.1870 nF (标称值: 330 nF)
```

随着 $R$ 的增大，系统特征值的实部（绝对值）逐渐增大，虚部逐渐减小。即衰减加快，震荡减慢。这符合从欠阻尼到临界阻尼的过渡。

可以看出，线性拟合结果很好，$R$ 几乎保持了线性，且 $\omega_n$ 也没有大的波动。

**step = 30 时**：

| 组号 | 实测R (Ω) | 特征根 | 阻尼比 ζ | 自然频率 ω_n (rad/s) | 等效电阻 R_est (Ω) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 0.9 | -3461.25 ± 54760.19i | 0.06 | 54869.47 | 6.95 |
| 2 | 14.7 | -10272.55 ± 54715.65i | 0.18 | 55671.61 | 20.32 |
| 3 | 25.0 | -15956.75 ± 51805.99i | 0.29 | 54207.74 | 32.41 |
| 4 | 44.4 | -26818.26 ± 48097.00i | 0.49 | 55068.51 | 53.62 |
| 5 | 69.9 | -37759.77 ± 43938.27i | 0.65 | 57934.20 | 71.76 |
| 6 | 103.0 | -54365.86 ± 0.00i | 1.00 | 54365.86 | 110.10 |

![80%ri|.step=30时线性拟合结果](2-拟合结果_step=30_converted.png)

```text
=== 线性拟合分析 ===
拟合方程: R_est = 0.958 * R + 13.021
决定系数 R² = 0.901564

=== 辨识反推结果 ===
平均辨识电感 L: 0.9362 mH (标称值: 1.0 mH)
平均辨识电容 C: 308.9337 nF (标称值: 330 nF)
```

对 `step` = 30 的组，结果差强人意，部分数据点的 $R$ 与拟合直线偏离过大，且拟合的斜率为 0.958，与理想的 1 有些偏差。

**step = 10 时**：

| 组号 | 实测R (Ω) | 特征根 λ | 阻尼比 ζ | 自然频率 ω_n (rad/s) | 等效电阻 R_est (Ω) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 0.9 | -3609.91 ± 54513.19i | 0.07 | 54632.59 | 7.27 |
| 2 | 14.7 | -13542.25 ± 0.00i | 1.00 | 13542.25 | 110.10 |
| 3 | 25.0 | -47841.22 ± 53299.10i | 0.67 | 71621.06 | 73.54 |
| 4 | 44.4 | -82297.96 ± 0.00i | 1.00 | 82297.96 | 110.10 |
| 5 | 69.9 | -55236.48 ± 0.00i | 1.00 | 55236.48 | 110.10 |
| 6 | 103.0 | -38983.16 ± 0.00i | 1.00 | 38983.16 | 110.10 |

![80%ri|.step=10时线性拟合结果](2-拟合结果_step=10_converted.png)

```text
=== 线性拟合分析 ===
拟合方程: R_est = 0.690 * R + 57.205
决定系数 R² = -0.370744

=== 辨识反推结果 ===
平均辨识电感 L: 1.5013 mH (标称值: 1.0 mH)
平均辨识电容 C: 495.4365 nF (标称值: 330 nF)
```

好了这一组已经完全不行了，从各种意义上来说……

## .结果分析 {#4}

由于 `step` = 50 的组效果最好，下面的分析均基于该组数据。

**① 阻尼比 $\zeta$ 随回路电阻 $R_{tot}$ 单调递增**：

随着滑动变阻器阻值增大，阻尼比也随之增大。最低阻值 $0.9 \mathrm{\Omega}$ 时 $\zeta = 0.0631$，最高阻值 $103.0 \mathrm{\Omega}$ 时 $\zeta = 1.0000$，达到临界阻尼。

且容易验证，$\zeta$ 大致与 $R_{est}$（回路总电阻）成正比。这与公式 $\zeta = \frac{R}{2} \sqrt{\frac{C}{L}}$ 保持一致。

**② 自然角频率 $\omega_n$ 基本稳定**：

5 组数据的 $\omega_n$ 在 $54000 \sim 55600 \mathrm{rad \cdot s^{-1}}$ 之间波动，只有一组例外地飙升到了 $58000 \mathrm{rad \cdot s^{-1}}$。这也与公式 $\omega_n = \frac{1}{\sqrt{LC}}$ 保持一致，$\omega_n$ 只与 $L, C$ 有关，与总电阻 $R$ 无关。

小幅波动可能来源于示波器采样噪声、器件寄生参数、数据截取与下采样误差。

**③ 实测电阻 $R$ 与辨识等效电阻 $R_{est}$ 线性拟合分析**：

拟合方程为 $R_{est} = 0.992 R + 6.549 \mathrm{\Omega}$，斜率接近 1，说明二者呈极强线性正相关。截距 $6.549 \mathrm{\Omega}$ 为固定偏移量，来源为导线电阻、电感线圈直流内阻、示波器输入内阻等寄生等效内阻。

**④ 电感、电容辨识结果与标称值对比**：

平均辨识电感 $L_{est} = 0.9915 \mathrm{mH}$，标称值 $L = 1.0 \mathrm{mH}$，相对误差 $0.85\%$。

平均辨识电容 $C_{est} = 327.1870 \mathrm{nF}$，标称值 $C = 330 \mathrm{nF}$，相对误差 $0.85\%$。

误差可能来源：

- 电路中存在其他寄生电阻；
- 示波器采样噪声、下采样等引入辨识偏差；
- 数据截取时仍保留了阶跃发生前的一小段信号（对应 $u(k) = 0$），但处理时与其他信号一视同仁为 $u(k) = 1$，造成误差；
- 标称值不一定准确（标称值一定是 $1.0 \mathrm{mH}, 330 \mathrm{nF}$ **这么整**的数吗？）

## .完整代码 {#5}

```matlab
clc; clear; close all;

R_true = [0.9, 14.7, 25.0, 44.4, 69.9, 103.0];  % 实测电阻值 
filenames = {'F0001CH1.csv', 'F0006CH1.csv', 'F0005CH1.csv', 'F0004CH1.csv', 'F0003CH1.csv', 'F0002CH1.csv'};
step = 10;  % 下采样间隔点数

figure('Name', '拟合结果检查');

valid_file_cnt = 0;
l = length(R_true);
[wn_list, zeta_list, R_list, R_est_list, lambda_real_list, lambda_imag_list] = deal(zeros(1, l));  % 都赋值为 1*l 向量

fprintf('=== 步长=%d ===\n', step);

%% 对每个文件进行参数辨识

for i = 1:length(filenames)
    % 检查文件是否存在
    filePath = fullfile('data_use', filenames{i});  % 文件位于 data_use/ 目录下
    if ~exist(filePath, 'file')
        fprintf('跳过 %s\n', filePath);
        continue;
    end

    % 读取数据
    data = readmatrix(filePath, 'NumHeaderLines', 18);  % 跳过 CSV 文件前 18 行标题
    t_raw = data(:, 4);
    y_raw = data(:, 5);

    valid_file_cnt = valid_file_cnt + 1;

    % 智能动态截取：寻找阶跃点并截取后续振荡段
    [~, jump_idx] = max(abs(diff(y_raw)));
    start_idx = max(1, jump_idx - 20);
    end_idx = min(length(y_raw), start_idx + 1200);

    y = y_raw(start_idx:end_idx);
    t = t_raw(start_idx:end_idx);

    % 下采样 (step=50 左右通常能获得最稳定的辨识结果)
    y = y(1:step:end);
    t = t(1:step:end);
    y = y - mean(y(end-20:end)); % 去直流

    % 最小二乘辨识
    Y = y(3:end);
    X = [-y(2:end-1), -y(1:end-2)];
    theta = pinv(X) * Y;

    % 数学法计算极点 (S平面)
    Ts = abs(mean(diff(t)));
    z_poles = roots([1, theta(1), theta(2)]); % 离散极点
    s_poles = log(z_poles) / Ts;              % 连续极点

    sigma = -real(s_poles(1));
    wd = abs(imag(s_poles(1)));
    wn_val = sqrt(sigma^2 + wd^2);
    zeta_val = sigma / wn_val;
    R_est = 2 * zeta_val * sqrt(1e-3 / 330e-9);
    
    R_list(valid_file_cnt) = R_true(i);
    wn_list(valid_file_cnt) = wn_val;
    zeta_list(valid_file_cnt) = zeta_val;
    R_est_list(valid_file_cnt) = R_est;
    lambda_real_list(valid_file_cnt) = real(s_poles(1));
    lambda_imag_list(valid_file_cnt) = imag(s_poles(1));

    % fprintf('\n=== 第 %d 组 | 实测 R=%.1fΩ | 文件名：%s ===\n', valid_file_cnt, R_true(i), filenames{i});
    % fprintf('特征根 lambda: %.4f ± %.4fi\n', lambda_real_list(valid_file_cnt), lambda_imag_list(valid_file_cnt));
    % fprintf('阻尼比 zeta: %.4f\n', zeta_val);
    % fprintf('自然频率 wn: %.2f rad/s\n', wn_val);
    % fprintf('等效电阻 R: %.2f Ω\n', R_est);

    % subplot(2,3,i);

    % 利用离散传递函数模拟
    sys_d = tf([0 0 1], [1, theta(1), theta(2)], Ts);
    y_fit = lsim(sys_d, zeros(size(y)), t, y(1:2));
    % plot(t, y, 'r', t, y_fit, 'b--');
    % title(['R=', num2str(R_true(i))]); grid on;
end

% pic_title = sprintf('1-各组结果汇总_step=%d.png', step);
% exportgraphics(gcf, pic_title, 'Resolution', 300); 

%% 拟合求解 R_fit

p = polyfit(R_list, R_est_list, 1);  % 拟合一阶多项式
k = p(1);
b = p(2);
R_fit = k * R_list + b;
R2 = 1 - sum((R_est_list - R_fit).^2) / sum((R_est_list - mean(R_est_list)).^2);

% figure;
% scatter(R_list, R_est_list, 'filled', 'MarkerFaceColor', 'r', 'DisplayName', '实测数据点'); hold on;
% plot(R_list, R_fit, 'b-', 'LineWidth', 1.5, 'DisplayName', '线性拟合直线');
% xlabel('实测变阻器电阻 R / Ω');
% ylabel('辨识出的等效电阻 R_{est} / Ω');
% title({['电阻辨识线性拟合: R_{est} = ', num2str(k, '%.2f'), 'R + ', num2str(b, '%.2f')]; ...
%        ['R^2 = ', num2str(R2, '%.4f')]});
% grid on;
% legend('show', 'Location', 'northwest');

% pic_title = sprintf('2-拟合结果_step=%d.png', step);
% exportgraphics(gcf, pic_title, 'Resolution', 300); 

fprintf('\n| 组号 | 实测R (Ω) | 特征根 λ | 阻尼比 ζ | 自然频率 ω_n (rad/s) | 等效电阻 R_est (Ω) |\n');
fprintf('| :---: | :---: | :---: | :---: | :---: | :---: |\n');
for i = 1:valid_file_cnt
    fprintf('| %d | %.1f | %.2f ± %.2fi | %.2f | %.2f | %.2f |\n', ...
        i, R_list(i), lambda_real_list(i), lambda_imag_list(i), zeta_list(i), wn_list(i), R_est_list(i));
end

% 显示方程参数
fprintf('\n=== 线性拟合分析 ===\n');
fprintf('拟合方程: R_est = %.3f * R + %.3f\n', k, b);
fprintf('决定系数 R² = %.6f\n', R2);

% 计算 L 和 C
L_est = R_est_list ./ (2 .* zeta_list .* wn_list);
C_est = (2 .* zeta_list) ./ (R_est_list .* wn_list);

% 排除第 2 组 (zeta=1 的临界阻尼组，计算会发散，一般建议排除)
idx = [1, 2, 3, 4, 5]; 
L_mean = mean(L_est(idx)) * 1e3; % 转为 mH
C_mean = mean(C_est(idx)) * 1e9; % 转为 nF

fprintf('\n=== 辨识反推结果 ===\n');
fprintf('平均辨识电感 L: %.4f mH (标称值: 1.0 mH)\n', L_mean);
fprintf('平均辨识电容 C: %.4f nF (标称值: 330 nF)\n', C_mean);
```
