{
  description = "CrossNote style generator for markdown-preview-enhanced";

  inputs.nix-vscode-extensions.url = "github:nix-community/nix-vscode-extensions";

  outputs = {self, nix-vscode-extensions, ...}: {
    homeManagerModules.mdcss = import ./module.nix;
    homeManagerModules.default = self.homeManagerModules.mdcss;
    homeManagerModules.markdown-preview-enhanced =
      import ./markdown-preview-enhanced.nix nix-vscode-extensions;
  };
}
