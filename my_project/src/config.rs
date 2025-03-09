// src/config.rs

use serde::Deserialize;
use std::{env, error::Error, fs, path::Path};
use log::{info, error};

/// Represents the application configuration.
#[derive(Debug, Deserialize)]
pub struct Config {
    pub api_key: String,
    pub google_drive_url: String,
    pub dropbox_url: String,
    pub download_timeout: u64,      // in seconds
    pub max_retries: u32,
    pub default_download_dir: String,
    pub debug: bool,
}

impl Default for Config {
    fn default() -> Self {
        Config {
            api_key: "".to_string(),
            google_drive_url: "https://www.googleapis.com/drive/v3".to_string(),
            dropbox_url: "https://api.dropboxapi.com/2".to_string(),
            download_timeout: 30,
            max_retries: 5,
            default_download_dir: "./Downloads".to_string(),
            debug: false,
        }
    }
}

impl Config {
    /// Loads configuration from "config.json" and overrides values with environment variables if available.
    /// Returns a validated `Config` instance or an error if critical values are missing.
    pub fn load() -> Result<Self, Box<dyn Error>> {
        let config_file = "config.json";
        let mut config = if Path::new(config_file).exists() {
            info!("Loading configuration from '{}'", config_file);
            let contents = fs::read_to_string(config_file)?;
            let cfg: Config = serde_json::from_str(&contents)?;
            info!("Configuration loaded successfully from file.");
            cfg
        } else {
            info!("Config file '{}' not found; using default configuration.", config_file);
            Config::default()
        };

        // Environment variable overrides
        for (env_var, update_fn) in [
            ("API_KEY", |c: &mut Config, val: String| c.api_key = val),
            ("GOOGLE_DRIVE_URL", |c: &mut Config, val: String| c.google_drive_url = val),
            ("DROPBOX_URL", |c: &mut Config, val: String| c.dropbox_url = val),
            ("DOWNLOAD_TIMEOUT", |c: &mut Config, val: String| {
                if let Ok(timeout) = val.parse::<u64>() {
                    c.download_timeout = timeout;
                }
            }),
            ("MAX_RETRIES", |c: &mut Config, val: String| {
                if let Ok(retries) = val.parse::<u32>() {
                    c.max_retries = retries;
                }
            }),
            ("DEFAULT_DOWNLOAD_DIR", |c: &mut Config, val: String| c.default_download_dir = val),
            ("DEBUG", |c: &mut Config, val: String| {
                c.debug = val.to_lowercase() == "true"
            }),
        ]
        .iter()
        {
            if let Ok(val) = env::var(env_var) {
                update_fn(&mut config, val);
                info!("Overrode {} from environment.", env_var);
            }
        }

        // Validate critical configuration values.
        if config.api_key.trim().is_empty() {
            error!("API_KEY is missing or empty in the configuration.");
            return Err("API_KEY is missing in configuration".into());
        }
        if config.default_download_dir.trim().is_empty() {
            error!("DEFAULT_DOWNLOAD_DIR is missing or empty in the configuration.");
            return Err("DEFAULT_DOWNLOAD_DIR is missing in configuration".into());
        }

        info!("Configuration loaded and validated successfully.");
        Ok(config)
    }
}
