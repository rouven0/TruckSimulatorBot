{ lib, stdenv, buildPythonPackage, fetchPypi, python311Packages, python, ... }:


stdenv.mkDerivation {
  pname = "trucksimulatorbot-docs";
  version = "0.0.1";
  src = ./.;

  propagatedBuildInputs = with python311Packages; [
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
        propagatedBuildInputs = [
          flask
          requests
          requests-toolbelt
          pynacl
          pytest
          quart
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
    homepage = "https://trucksimulatorbot.rfive.de/docs";
    platforms = platforms.all;
    maintainers = with maintainers; [ therealr5 ];
  };
}
