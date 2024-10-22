use axum::{routing::post, Router};
use helpers::get_or_create_stream;
use pay::handle_payment;
use state::AppState;
use std::env;

mod data;
mod pay;
mod state;
mod helpers;


#[tokio::main]
async fn main() {
    let state = AppState::new().await;
    get_or_create_stream("events".to_string(), vec!["events.>".to_string()]).await.expect("stream creation failed");
    let app = Router::new()
        .route("/pay", post(handle_payment))
        .with_state(state);

    let port: i32 = env::var("PAYMENT_PORT")
        .unwrap_or("3000".to_string())
        .parse()
        .unwrap();
    let listener = tokio::net::TcpListener::bind(&format!("0.0.0.0:{}", port))
        .await
        .unwrap();
    axum::serve(listener, app).await.unwrap();
}
