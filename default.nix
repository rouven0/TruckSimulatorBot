{ buildPythonPackage, fetchPypi, python-i18n, mysql-connector, gunicorn, pyyaml, flask, requests, requests-toolbelt, pynacl, pytest, python, setuptools, ... }:

buildPythonPackage {
  name = "TruckSimulatorBot";
  src = ./trucksimulator;

  propagatedBuildInputs = [
    python-i18n
    mysql-connector
    gunicorn
    pyyaml
    (buildPythonPackage
      rec {
        pname = "Flask-Discord-Interactions";
        version = "2.1.2";
        pyproject = true;
        build-system = [ setuptools ];

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
    mkdir -p $out/${python.sitePackages}
    cp -r . $out/${python.sitePackages}/trucksimulator
    runHook postInstall '';

  shellHook = "export FLASK_APP=trucksimulator";

  format = "other";
}
