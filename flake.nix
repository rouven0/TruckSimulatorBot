{
  description = "The Truck Simulator Discord bot";
  inputs = {
    images = {
      url = "sourcehut:~rouven/trucksimulator-images";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs @ { self, nixpkgs, images }:
    let
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      pkgs = forAllSystems (system: nixpkgs.legacyPackages.${system});
    in
    {
      packages = forAllSystems (system: {
        default = pkgs.${system}.python311Packages.callPackage ./default.nix { };
        docs = pkgs.${system}.python311Packages.callPackage ./docs.nix { };
      });
      nixosModules.default = import ./module.nix inputs;

      devShells = forAllSystems (system: {
        default =
          let
            pythonEnv = pkgs.${system}.python311.withPackages (p: with p; [
              gunicorn
              sphinx
              (self.packages.${system}.default)

              (buildPythonPackage
                rec {
                  pname = "sphinx-readable-theme";
                  version = "1.3.0";

                  src = fetchPypi {
                    inherit pname version;
                    sha256 = "9f5louESy5VrNm30Hg/IlP9rbw5KSBT8v/aSVm20f8A=";
                  };
                })

            ]);
          in

          pkgs.${system}.mkShell {
            packages = [ pythonEnv ];
            shellHook = ''
              export PYTHONPATH="${pythonEnv}/lib/python3.11/site-packages/"
            '';
          };
      });
    };
}
