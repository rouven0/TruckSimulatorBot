inputs: { lib, pkgs, config, ... }:
with lib;
let
  cfg = config.services.trucksimulatorbot;
  appEnv = pkgs.python3.withPackages (p: with p; [ gunicorn (pkgs.python310Packages.callPackage ./default.nix { }) ]);
  imageEnv = pkgs.python3.withPackages (p: with p; [ gunicorn inputs.images.packages.x86_64-linux.default ]);
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
    discord.clientId = mkOption {
      type = types.str;
      description = mdDoc ''
        Client id to use with discord.
      '';
    };
    discord.publicKey = mkOption {
      type = types.str;
      description = mdDoc ''
        Public key to verify requests.
      '';
    };
    images.listenPort = mkOption {
      type = types.port;
      default = 9001;
      description = mdDoc ''
        Port the image-server will run on.
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
      environment = {
        DISCORD_CLIENT_ID = cfg.discord.clientId;
        DISCORD_PUBLIC_KEY = cfg.discord.publicKey;
      };
      serviceConfig = {
        ExecStart = "${appEnv}/bin/gunicorn trucksimulator:app -b 0.0.0.0:${toString cfg.listenPort} --error-logfile -";
        User = "trucksimulatorbot";
        Group = "trucksimulatorbot";
      };
    };
    systemd.services.trucksimulatorbot-images = {
      enable = true;
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        ExecStart = "${imageEnv}/bin/gunicorn trucksimulatorbot-images:app -b 0.0.0.0:${toString cfg.images.listenPort} --error-logfile -";
        User = "trucksimulatorbot";
        Group = "trucksimulatorbot";
      };
    };
  };
}
