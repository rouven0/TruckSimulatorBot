{ self, lib, pkgs, config, ... }:
with lib;
let
  cfg = config.services.trucksimulatorbot.images;
  appEnv = pkgs.python3.withPackages (p: with p; [ gunicorn (pkgs.python310Packages.callPackage ./default.nix { }) ]);
in
{
  options.services.trucksimulatorbot = {
    enable = mkEnableOption "Trucksimulatorbot";
    listenPort = mkOption {
      type = types.port;
      default = 9000;
      description = mdDoc ''
        Port the app will run on.
      '';
    };
  };

  config = mkIf (cfg.enable) {
    users.users.trucksimulatorbot = {
      isSystemUser = true;
      group = "trucksimulatorbot";
    };
    users.groups.trucksimulatorbot = { };

    systemd.services.trucksimulatorbot = {
      enable = true;
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        ExecStart = "${appEnv}/bin/gunicorn trucksimulatorbot:app -b 0.0.0.0:${toString cfg.listenPort} --error-logfile -";
        User = "trucksimulatorbot";
        Group = "trucksimulatorbot";
      };
    };
  };
}
