{ pkgs ? import <nixpkgs> { } }:
pkgs.mkShell {
  nativeBuildInputs = with pkgs.python310Packages; [
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
}
