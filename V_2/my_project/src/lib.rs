use reqwest::{blocking::Client, header::{AUTHORIZATION}};
use serde::{Deserialize, Serialize};
use std::error::Error;
use chrono::{Utc, DateTime};
use chrono::serde::ts_seconds;
use std::fs::File;
use std::io;
use log::{info, error};

#[derive(Debug, Serialize, Deserialize)]
pub struct AuthTokens {
    pub access_token: String,
    pub refresh_token: Option<String>,
    #[serde(with = "ts_seconds")]
    pub expires_at: DateTime<Utc>,
}

pub struct AuthManager {
    pub access_token: Option<String>,
    pub refresh_token: Option<String>,
    pub expires_at: Option<DateTime<Utc>>,
}

impl AuthManager {
    pub fn new() -> Self {
        AuthManager {
            access_token: None,
            refresh_token: None,
            expires_at: None,
        }
    }

    pub fn authenticate(&mut self, auth_code: &str, client_id: &str, client_secret: &str, redirect_uri: &str) -> Result<(), Box<dyn Error>> {
        info!("Starting authentication process with provided authorization code.");

        let token_url = "https://oauth2.googleapis.com/token";
        let params = [
            ("code", auth_code),
            ("client_id", client_id),
            ("client_secret", client_secret),
            ("redirect_uri", redirect_uri),
            ("grant_type", "authorization_code")
        ];
        
        let client = Client::new();
        let response = client.post(token_url).form(&params).send()?;

        if !response.status().is_success() {
            return Err(format!("Failed to exchange authorization code for tokens: {}", response.status()).into());
        }

        let tokens: AuthTokens = match response.json() {
            Ok(tokens) => tokens,
            Err(e) => {
                error!("Failed to parse tokens from response: {}", e);
                return Err(format!("Failed to parse tokens from response: {}", e).into());
            }
        };

        self.access_token = Some(tokens.access_token.clone());
        self.refresh_token = tokens.refresh_token.clone();
        self.expires_at = Some(tokens.expires_at);

        self.store_tokens(&tokens)?;

        info!("Authentication successful, tokens stored securely.");
        Ok(())
    }

    fn store_tokens(&self, tokens: &AuthTokens) -> Result<(), io::Error> {
        let file_path = std::path::Path::new("auth_tokens.json");
        let file = File::create(file_path)?;
        serde_json::to_writer(file, &tokens)?;
        info!("Tokens stored to file 'auth_tokens.json'.");
        Ok(())
    }

    pub fn load_tokens(&mut self) -> Result<(), io::Error> {
        let file_path = std::path::Path::new("auth_tokens.json");
        if file_path.exists() {
            let file = File::open(file_path)?;
            let tokens: AuthTokens = serde_json::from_reader(file)?;

            self.access_token = Some(tokens.access_token);
            self.refresh_token = tokens.refresh_token;
            self.expires_at = Some(tokens.expires_at);

            info!("Tokens loaded from file.");
            Ok(())
        } else {
            error!("No tokens found in 'auth_tokens.json'.");
            Err(io::Error::new(io::ErrorKind::NotFound, "No tokens found"))
        }
    }

    pub fn refresh_access_token(&mut self, client_id: &str, client_secret: &str) -> Result<(), Box<dyn Error>> {
        if let Some(refresh_token) = &self.refresh_token {
            let token_url = "https://oauth2.googleapis.com/token";
            let params = [
                ("client_id", client_id),
                ("client_secret", client_secret),
                ("refresh_token", refresh_token),
                ("grant_type", "refresh_token")
            ];
            
            let client = Client::new();
            let response = client.post(token_url).form(&params).send()?;

            if !response.status().is_success() {
                return Err(format!("Failed to refresh the access token: {}", response.status()).into());
            }

            let new_tokens: AuthTokens = response.json()?;

            self.access_token = Some(new_tokens.access_token.clone());
            self.refresh_token = new_tokens.refresh_token.clone();
            self.expires_at = Some(new_tokens.expires_at);

            self.store_tokens(&new_tokens)?;

            info!("Access token refreshed successfully.");
            Ok(())
        } else {
            Err("No refresh token available".into())
        }
    }

    pub fn is_token_expired(&self) -> bool {
        if let Some(expiry_time) = &self.expires_at {
            Utc::now() > *expiry_time
        } else {
            true
        }
    }

    pub fn add_authorization_header(&self, req: reqwest::blocking::RequestBuilder) -> Result<reqwest::blocking::RequestBuilder, Box<dyn Error>> {
        if let Some(ref access_token) = self.access_token {
            let req = req.header(AUTHORIZATION, format!("Bearer {}", access_token));
            Ok(req)
        } else {
            Err("No access token available".into())
        }
    }
}