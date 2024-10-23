use std::time::Duration;

use axum::{extract::State, Json};
use serde::Serialize;
use serde_json::json;
use tokio::time::sleep;

use crate::{data::PaymentPayload, state::AppState};

#[derive(Serialize)]
struct Response{
    message: &'static str 
}

pub async fn handle_payment(
    State(state): State<AppState>,
    Json(payload): Json<PaymentPayload>,
) -> Result<String, &'static str> {
    println!("Starting payment processing for order ID: {}", payload.order_id);
    
    // Simulate a delay to mimic payment processing
    sleep(Duration::from_millis(500)).await;
    println!("Payment processing completed for order ID: {}", payload.order_id);
    
    let subject = "events.paid";
    let message = json!({ "order_id": payload.order_id });
    
    println!("Serializing message for NATS: {:?}", message);
    let message_bytes = serde_json::to_vec(&message)
        .map_err(|_| {
            println!("Failed to serialize message");
            "Failed to serialize message"
        })?;
    
    println!("Publishing message to NATS on subject: {}", subject);
    state
        .nats_connection
        .publish(subject, message_bytes.into())
        .await
        .map_err(|_| {
            println!("Failed to publish to NATS");
            "Failed to publish to NATS"
        })?;
    
    println!("Payment processed and event published for order ID: {}", payload.order_id);
    let res = Response{message: "Payment processed and event published"};
    serde_json::to_string(&res).map_err(|_| "serialization failed")
}
