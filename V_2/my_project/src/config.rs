use serde::Deserialize;
use std::env;
use std::error::Error;
use std::fs;
use std::path::Path;

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

impl Config {
    /// Load configuration from a JSON file ("config.json") and override with environment variables if available.
    pub fn load() -> Result<Self, Box<dyn Error>> {
        let config_file = "config.json";
        // Load default configuration from file if it exists; otherwise, use default values.
        let mut config: Config = if Path::new(config_file).exists() {
            let contents = fs::read_to_string(config_file)?;
            serde_json::from_str(&contents)?
        } else {
            // Provide default values (could be refined further)
            Config {
                api_key: "".to_string(),
                google_drive_url: "https://www.googleapis.com/drive/v3".to_string(),
                dropbox_url: "https://api.dropboxapi.com/2".to_string(),
                download_timeout: 30,
                max_retries: 5,
                default_download_dir: "./Downloads".to_string(),
                debug: false,
            }
        };

        // Override configuration with environment variables if they exist.
        if let Ok(api_key) = env::var("API_KEY") {
            config.api_key = api_key;
        }
        if let Ok(g_drive_url) = env::var("GOOGLE_DRIVE_URL") {
            config.google_drive_url = g_drive_url;
        }
        if let Ok(dropbox_url) = env::var("DROPBOX_URL") {
            config.dropbox_url = dropbox_url;
        }
        if let Ok(timeout) = env::var("DOWNLOAD_TIMEOUT") {
            config.download_timeout = timeout.parse()?;
        }
        if let Ok(retries) = env::var("MAX_RETRIES") {
            config.max_retries = retries.parse()?;
        }
        if let Ok(dir) = env::var("DEFAULT_DOWNLOAD_DIR") {
            config.default_download_dir = dir;
        }
        if let Ok(debug_flag) = env::var("DEBUG") {
            config.debug = debug_flag.to_lowercase() == "true";
        }

        // Validate critical configuration values.
        if config.api_key.trim().is_empty() {
            return Err("API_KEY is missing in configuration".into());
        }
        if config.default_download_dir.trim().is_empty() {
            return Err("DEFAULT_DOWNLOAD_DIR is missing in configuration".into());
        }

        Ok(config)
    }
}
