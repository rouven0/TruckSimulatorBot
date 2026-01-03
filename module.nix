inputs: { lib, pkgs, config, ... }:
with lib;
let
  cfg = config.services.trucksimulatorbot;
  appEnv = pkgs.python3.withPackages (p: with p; [ gunicorn (pkgs.python3Packages.callPackage ./default.nix { }) ]);
  imageEnv = pkgs.python3.withPackages (p: with p; [ gunicorn inputs.images.packages.x86_64-linux.default ]);
in
{
  options.services.trucksimulatorbot = {
    enable = mkEnableOption "Trucksimulatorbot";
    domain = mkOption {
      type = types.str;
      description = mdDoc ''
        Domain name the app runs under.
      '';
    };
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
    database = {
      name = mkOption {
        type = types.str;
        default = "trucksimulator";
        description = mdDoc ''
          Database name
        '';
      };
      user = mkOption {
        type = types.str;
        default = "trucksimulator";
        description = mdDoc ''
          Database user
        '';
      };
      socketPath = mkOption {
        type = types.path;
        default = "/run/mysqld/mysqld.sock";
        description = mdDoc ''
          Database unix socket path
        '';
      };


    };
  };

  config = mkIf (cfg.enable) {
    systemd.sockets.trucksimulator = {
      wantedBy = [ "sockets.target" ];
      before = [ "nginx.service" ];
      socketConfig.ListenStream = "/run/trucksimulator/app.sock";
    };
    systemd.services.trucksimulator = {
      enable = true;
      after = [ "network.target" ];
      requires = [ "trucksimulator.socket" ];
      environment = {
        DISCORD_CLIENT_ID = cfg.discord.clientId;
        DISCORD_PUBLIC_KEY = cfg.discord.publicKey;
        MYSQL_USER = cfg.database.user;
        MYSQL_DATABASE = cfg.database.name;
        MYSQL_SOCKET = cfg.database.socketPath;

      };
      serviceConfig = {
        DynamicUser = true;
        ExecStart = "${appEnv}/bin/gunicorn trucksimulator:app -b /run/trucksimulator/app.sock --error-logfile -";
      };
    };
    systemd.sockets.trucksimulator-images = {
      wantedBy = [ "sockets.target" ];
      before = [ "nginx.service" ];
      socketConfig.ListenStream = "/run/trucksimulator/images.sock";
    };
    systemd.services.trucksimulator-images = {
      enable = true;
      after = [ "network.target" ];
      requires = [ "trucksimulator-images.socket" ];
      serviceConfig = {
        DynamicUser = true;
        ExecStart = "${imageEnv}/bin/gunicorn trucksimulatorbot-images:app -b /run/trucksimulator/images.sock --error-logfile -";
      };
    };
  };
}
