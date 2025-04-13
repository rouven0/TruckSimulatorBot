{ lib, stdenv, buildPythonPackage, sphinx, python-i18n, mysql-connector, pyyaml, gunicorn, flask, requests, requests-toolbelt, pynacl, pytest, fetchPypi, ... }:


stdenv.mkDerivation {
  pname = "trucksimulatorbot-docs";
  version = "0.0.1";
  src = ./.;

  propagatedBuildInputs = [
    sphinx
    (buildPythonPackage
      rec {
        pname = "sphinx-readable-theme";
        version = "1.3.0";

        src = fetchPypi {
          inherit pname version;
          sha256 = "9f5louESy5VrNm30Hg/IlP9rbw5KSBT8v/aSVm20f8A=";
        };
      })

    python-i18n
    mysql-connector
    gunicorn
    pyyaml
    (buildPythonPackage
      rec {
        pname = "Flask-Discord-Interactions";
        version = "2.1.2";
        # tests require quart, which is currently broken
        doCheck = false;
        propagatedBuildInputs = [
          flask
          requests
          requests-toolbelt
          pynacl
          pytest
        ];

        src = fetchPypi {
          inherit pname version;
          sha256 = "3jN0RcArARN1nt6pZTPQS7ZglFUE17ZSpLcsOX49gLM=";
        };
      })
  ];

  installPhase = ''
    runHook preInstall
    mkdir -p $out/docs
    # cd ./trucksimulator
    sphinx-build ./docs/ $out/docs
    runHook postInstall
  '';

  meta = with lib; {
    description = "Truck Simulator docs";
    homepage = "https://trucks.rfive.de/docs";
    platforms = platforms.all;
    maintainers = with maintainers; [ therealr5 ];
  };
}
