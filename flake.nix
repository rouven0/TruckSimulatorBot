{
  description = "The Truck Simulator Discord bot";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      pkgs = forAllSystems (system: nixpkgs.legacyPackages.${system});
    in
    {
      packages = forAllSystems (system: {
        default = pkgs.${system}.python310Packages.callPackage ./default.nix { };
        docs = pkgs.${system}.python310Packages.callPackage ./docs.nix { };
      });
      nixosModules.default = import ./module.nix;

      devShells = forAllSystems (system: {
        default = pkgs.${system}.mkShellNoCC {
          packages = with pkgs.${system}.python310Packages; [
            python-i18n
            mysql-connector
            gunicorn
            pyyaml
            (buildPythonPackage
              rec {
                pname = "Flask-Discord-Interactions";
                version = "2.1.2";
                propagatedBuildInputs = [
                  flask
                  requests
                  requests-toolbelt
                  pynacl
                  pytest
                  (buildPythonPackage
                    rec {
                      pname = "quart";
                      version = "0.18.4";
                      propagatedBuildInputs = [
                        flask
                        hypercorn
                        markupsafe
                        blinker
                        aiofiles
                      ];

                      src = fetchPypi {
                        inherit pname version;
                        sha256 = "wXZvJpzbhdr52me6VBcKv3g5rKlzBNy0zQd46r+0QsY=";
                      };
                    })
                ];

                src = fetchPypi {
                  inherit pname version;
                  sha256 = "3jN0RcArARN1nt6pZTPQS7ZglFUE17ZSpLcsOX49gLM=";
                };
              })
          ];
        };
      });
    };
}
