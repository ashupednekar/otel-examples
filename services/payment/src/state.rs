use async_nats::Client;

use crate::helpers::get_nats_connection;

#[derive(Clone, Debug)]
pub struct AppState {
    pub nats_connection: Client,
}

impl AppState {
    pub async fn new() -> Self {
        Self {
            nats_connection: get_nats_connection().await.unwrap(),
        }
    }
}
