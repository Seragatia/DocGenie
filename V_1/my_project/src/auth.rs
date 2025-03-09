use std::collections::HashMap;
use std::fs::{self, File};
use std::io::{self, Write};
use std::path::Path;
use reqwest::header::{HeaderMap, AUTHORIZATION};
use reqwest::blocking::{Client, Response};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::error::Error;
use chrono::{Utc, DateTime, Duration};

#[derive(Debug, Serialize, Deserialize)]
pub struct AuthTokens {
    access_token: String,
    refresh_token: Option<String>,
    expires_at: DateTime<Utc>,
}

pub struct AuthManager {
    access_token: Option<String>,
    refresh_token: Option<String>,
    expires_at: Option<DateTime<Utc>>,
}

impl AuthManager {
    pub fn new() -> Self {
        AuthManager {
            access_token: None,
            refresh_token: None,
            expires_at: None,
        }
    }

    // Function to initiate OAuth process and obtain tokens.
    pub fn authenticate(&mut self, auth_code: &str, client_id: &str, client_secret: &str, redirect_uri: &str) -> Result<(), Box<dyn Error>> {
        // 1. Exchange the authorization code for an access token
        let token_url = "https://oauth2.googleapis.com/token";  // Example URL for OAuth2 token exchange
        let params = [
            ("code", auth_code),
            ("client_id", client_id),
            ("client_secret", client_secret),
            ("redirect_uri", redirect_uri),
            ("grant_type", "authorization_code")
        ];
        
        let client = Client::new();
        let response = client.post(token_url)
            .form(&params)
            .send()?;

        let tokens: AuthTokens = response.json()?;

        self.access_token = Some(tokens.access_token);
        self.refresh_token = tokens.refresh_token;
        self.expires_at = Some(tokens.expires_at);

        // Store the tokens securely (e.g., in a file or encrypted store)
        self.store_tokens(&tokens)?;

        Ok(())
    }

    // Store the obtained tokens in a file
    fn store_tokens(&self, tokens: &AuthTokens) -> Result<(), io::Error> {
        let file_path = Path::new("auth_tokens.json");
        let file = File::create(file_path)?;
        serde_json::to_writer(file, &tokens)?;
        Ok(())
    }

    // Load stored tokens from a file
    pub fn load_tokens(&mut self) -> Result<(), io::Error> {
        let file_path = Path::new("auth_tokens.json");
        if file_path.exists() {
            let file = File::open(file_path)?;
            let tokens: AuthTokens = serde_json::from_reader(file)?;

            self.access_token = Some(tokens.access_token);
            self.refresh_token = tokens.refresh_token;
            self.expires_at = Some(tokens.expires_at);

            Ok(())
        } else {
            Err(io::Error::new(io::ErrorKind::NotFound, "No tokens found"))
        }
    }

    // Refresh the access token using the refresh token.
    pub fn refresh_access_token(&mut self, client_id: &str, client_secret: &str) -> Result<(), Box<dyn Error>> {
        if let Some(refresh_token) = &self.refresh_token {
            let token_url = "https://oauth2.googleapis.com/token";  // Example URL for token refresh
            let params = [
                ("client_id", client_id),
                ("client_secret", client_secret),
                ("refresh_token", refresh_token),
                ("grant_type", "refresh_token")
            ];
            
            let client = Client::new();
            let response = client.post(token_url)
                .form(&params)
                .send()?;

            let new_tokens: AuthTokens = response.json()?;

            self.access_token = Some(new_tokens.access_token);
            self.refresh_token = new_tokens.refresh_token;
            self.expires_at = Some(new_tokens.expires_at);

            // Optionally store new tokens
            self.store_tokens(&new_tokens)?;

            Ok(())
        } else {
            Err("No refresh token available".into())
        }
    }

    // Function to verify if the token is expired and needs refreshing.
    pub fn is_token_expired(&self) -> bool {
        if let Some(expiry_time) = &self.expires_at {
            Utc::now() > *expiry_time
        } else {
            true // If there's no expiry time, treat as expired.
        }
    }

    // Function to add the authorization header to requests.
    pub fn add_authorization_header(&self, req: &mut reqwest::blocking::RequestBuilder) -> Result<(), Box<dyn Error>> {
        if let Some(access_token) = &self.access_token {
            req.header(AUTHORIZATION, format!("Bearer {}", access_token));
            Ok(())
        } else {
            Err("No access token available".into())
        }
    }
}

// Example usage of API key
pub fn get_with_api_key(url: &str, api_key: &str) -> Result<Response, Box<dyn Error>> {
    let client = Client::new();
    let mut req = client.get(url);
    req.header("Authorization", format!("Bearer {}", api_key));  // Example using an API key in the Authorization header
    let response = req.send()?;

    Ok(response)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_oauth_authentication() {
        // Replace with actual test OAuth code and valid credentials
        let auth_code = "test_auth_code";
        let client_id = "test_client_id";
        let client_secret = "test_client_secret";
        let redirect_uri = "test_redirect_uri";

        let mut auth_manager = AuthManager::new();
        let result = auth_manager.authenticate(auth_code, client_id, client_secret, redirect_uri);
        assert!(result.is_ok(), "Authentication should succeed");
    }

    #[test]
    fn test_token_expiry_check() {
        let mut auth_manager = AuthManager::new();
        // Simulate expired token
        auth_manager.expires_at = Some(Utc::now() - Duration::days(1));
        assert!(auth_manager.is_token_expired(), "Token should be expired");

        // Simulate valid token
        auth_manager.expires_at = Some(Utc::now() + Duration::days(1));
        assert!(!auth_manager.is_token_expired(), "Token should not be expired");
    }

    #[test]
    fn test_api_key_usage() {
        // Replace with an actual URL and API key for testing
        let api_key = "test_api_key";
        let url = "https://example.com/api";
        let result = get_with_api_key(url, api_key);
        assert!(result.is_ok(), "API request with API key should succeed");
    }
}
