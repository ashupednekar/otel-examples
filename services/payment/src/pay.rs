use std::time::Duration;

use axum::{extract::State, Json};
use opentelemetry::trace::{Span, Tracer};
use tracing;

use serde::Serialize;
use serde_json::json;
use tokio::time::sleep;

use crate::{data::PaymentPayload, state::AppState};

#[derive(Serialize)]
struct Response {
    message: &'static str,
}

#[tracing::instrument]
async fn produce(payload: &PaymentPayload, state: AppState) -> Result<(), &'static str> {
    let subject = "events.paid";
    let message = json!({ "order_id": payload.order_id });

    tracing::info!("Serializing message for NATS: {:?}", message);
    let message_bytes = serde_json::to_vec(&message).map_err(|_| {
        tracing::info!("Failed to serialize message");
        "Failed to serialize message"
    })?;

    tracing::info!("Publishing message to NATS on subject: {}", subject);
    state
        .nats_connection
        .publish(subject, message_bytes.into())
        .await
        .map_err(|_| {
            tracing::info!("Failed to publish to NATS");
            "Failed to publish to NATS"
        })?;
    Ok(())
}

pub async fn handle_payment(
    State(state): State<AppState>,
    Json(payload): Json<PaymentPayload>,
) -> Result<String, &'static str> {
    let tracer = opentelemetry::global::tracer("payment");

    tracing::info!(
        "Starting payment processing for order ID: {}",
        payload.order_id
    );

    let mut span = tracer
        .span_builder("processing payment".to_string())
        .start(&tracer);

    sleep(Duration::from_millis(500)).await;
    tracing::info!(
        "Payment processing completed for order ID: {}",
        payload.order_id
    );

    Span::end(&mut span);

    let s = tracing::span!(tracing::Level::INFO, "AAA");
    let _ = s.enter();
    let s1 = tracing::span!(tracing::Level::INFO, "aaa");
    let _ = s1.enter();
    sleep(Duration::from_millis(100)).await;
    drop(s1);
    sleep(Duration::from_millis(100)).await;
    drop(s);

    produce(&payload, state).await?;

    tracing::info!(
        "Payment processed and event published for order ID: {}",
        payload.order_id
    );
    let res = Response {
        message: "Payment processed and event published",
    };
    serde_json::to_string(&res).map_err(|_| "serialization failed")
}
