// my_project/src/auth.rs

use reqwest::blocking::Client;
use chrono::{Utc, DateTime};
use chrono::serde::ts_seconds;
use serde::{Deserialize, Serialize};
use log::{info, error, debug};
use std::error::Error;
use std::fs;
use std::path::Path;

/// Structure representing the authentication tokens.
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AuthTokens {
    pub access_token: String,
    pub refresh_token: Option<String>,
    #[serde(with = "ts_seconds")]
    pub expires_at: DateTime<Utc>,
}

/// Manager for handling authentication tokens.
pub struct AuthManager {
    pub access_token: Option<String>,
    pub refresh_token: Option<String>,
    pub expires_at: Option<DateTime<Utc>>,
}

impl AuthManager {
    /// Creates a new instance of AuthManager with no tokens.
    pub fn new() -> Self {
        AuthManager {
            access_token: None,
            refresh_token: None,
            expires_at: None,
        }
    }

    /// Returns true if the current access token is expired or missing.
    pub fn is_token_expired(&self) -> bool {
        if let Some(expiry) = &self.expires_at {
            let expired = Utc::now() > *expiry;
            debug!("Token expiry time: {}", expiry);
            debug!("Current time: {}", Utc::now());
            if expired {
                info!("Token expired.");
            }
            expired
        } else {
            info!("No token available; treating as expired.");
            true
        }
    }

    /// Refreshes the access token using the stored refresh token.
    ///
    /// # Arguments
    ///
    /// * `client_id` - The OAuth client ID.
    /// * `client_secret` - The OAuth client secret.
    ///
    /// # Errors
    ///
    /// Returns an error if the refresh token is missing, the network request fails,
    /// or the token refresh response indicates a failure.
    pub fn refresh_access_token(
        &mut self,
        client_id: &str,
        client_secret: &str,
    ) -> Result<(), Box<dyn Error>> {
        if let Some(refresh_token) = &self.refresh_token {
            info!("Refreshing the access token using refresh token...");
            let client = Client::new();
            let token_url = "https://oauth2.googleapis.com/token";
            let params = [
                ("client_id", client_id),
                ("client_secret", client_secret),
                ("refresh_token", refresh_token),
                ("grant_type", "refresh_token"),
            ];

            let response = client.post(token_url).form(&params).send()?;
            debug!("Received response with status: {}", response.status());

            if !response.status().is_success() {
                let err_msg = format!("Failed to refresh token: HTTP {}", response.status());
                error!("{}", err_msg);
                return Err(err_msg.into());
            }

            let new_tokens: AuthTokens = response.json().map_err(|e| {
                let parse_err = format!("Failed to parse refresh response JSON: {}", e);
                error!("{}", parse_err);
                parse_err
            })?;

            // Update manager with new tokens.
            self.access_token = Some(new_tokens.access_token.clone());
            self.refresh_token = new_tokens.refresh_token.clone();
            self.expires_at = Some(new_tokens.expires_at);
            info!("Access token refreshed successfully.");

            // Persist tokens to file.
            self.store_tokens(&new_tokens)?;

            Ok(())
        } else {
            error!("No refresh token available. Cannot refresh access token.");
            Err("No refresh token available".into())
        }
    }

    /// Exchanges an authorization code for tokens.
    ///
    /// # Arguments
    ///
    /// * `auth_code` - The authorization code received from the OAuth provider.
    /// * `client_id` - The OAuth client ID.
    /// * `client_secret` - The OAuth client secret.
    /// * `redirect_uri` - The redirect URI registered with the OAuth provider.
    ///
    /// # Errors
    ///
    /// Returns an error if the exchange fails or if the response indicates a failure.
    pub fn authenticate(
        &mut self,
        auth_code: &str,
        client_id: &str,
        client_secret: &str,
        redirect_uri: &str,
    ) -> Result<(), Box<dyn Error>> {
        info!("Starting authentication process using authorization code.");

        let token_url = "https://oauth2.googleapis.com/token";
        let params = [
            ("code", auth_code),
            ("client_id", client_id),
            ("client_secret", client_secret),
            ("redirect_uri", redirect_uri),
            ("grant_type", "authorization_code"),
        ];

        let client = Client::new();
        let response = client.post(token_url).form(&params).send()?;
        debug!("Received response with status: {}", response.status());

        if !response.status().is_success() {
            let err_msg = format!("Failed to exchange authorization code for tokens: HTTP {}", response.status());
            error!("{}", err_msg);
            return Err(err_msg.into());
        }

        let tokens: AuthTokens = response.json().map_err(|e| {
            let parse_err = format!("Failed to parse authentication response JSON: {}", e);
            error!("{}", parse_err);
            parse_err
        })?;

        self.access_token = Some(tokens.access_token.clone());
        self.refresh_token = tokens.refresh_token.clone();
        self.expires_at = Some(tokens.expires_at);
        self.store_tokens(&tokens)?;
        info!("Authentication successful; tokens stored.");
        Ok(())
    }

    /// Stores the provided tokens in "auth_tokens.json".
    fn store_tokens(&self, tokens: &AuthTokens) -> Result<(), std::io::Error> {
        let file_path = Path::new("auth_tokens.json");
        let file = fs::File::create(file_path)?;
        serde_json::to_writer(file, tokens)?;
        info!("Tokens stored in 'auth_tokens.json'.");
        Ok(())
    }

    /// Loads tokens from "auth_tokens.json" if it exists.
    pub fn load_tokens(&mut self) -> Result<(), std::io::Error> {
        let file_path = Path::new("auth_tokens.json");
        if file_path.exists() {
            let file = fs::File::open(file_path)?;
            let tokens: AuthTokens = serde_json::from_reader(file)?;
            self.access_token = Some(tokens.access_token);
            self.refresh_token = tokens.refresh_token;
            self.expires_at = Some(tokens.expires_at);
            info!("Tokens loaded from 'auth_tokens.json'.");
            Ok(())
        } else {
            error!("No tokens found in 'auth_tokens.json'.");
            Err(std::io::Error::new(std::io::ErrorKind::NotFound, "No tokens found"))
        }
    }
}
