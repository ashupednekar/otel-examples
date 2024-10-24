use std::time::Duration;

use axum::{extract::State, Json};
use opentelemetry::{
    global::{self, ObjectSafeSpan},
    trace::{Span, SpanKind, Status, Tracer},
};
use tracing;

use serde::Serialize;
use serde_json::json;
use tokio::time::sleep;

use crate::{data::PaymentPayload, state::AppState};

#[derive(Serialize)]
struct Response {
    message: &'static str,
}

pub async fn handle_payment(
    State(state): State<AppState>,
    Json(payload): Json<PaymentPayload>,
) -> Result<String, &'static str> {
    let tracer = global::tracer("payment");

    let mut span = tracer
        .span_builder("payment processing".to_string())
        .with_kind(SpanKind::Internal)
        .start(&tracer);

    tracing::info!(
        "Starting payment processing for order ID: {}",
        payload.order_id
    );

    // Simulate a delay to mimic payment processing
    sleep(Duration::from_millis(500)).await;
    tracing::info!(
        "Payment processing completed for order ID: {}",
        payload.order_id
    );

    Span::set_status(&mut span, Status::Ok);
    Span::end(&mut span);

    let mut span = tracer
        .span_builder("producing paid event".to_string())
        .with_kind(SpanKind::Producer)
        .start(&tracer);

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

    Span::end(&mut span);

    tracing::info!(
        "Payment processed and event published for order ID: {}",
        payload.order_id
    );
    let res = Response {
        message: "Payment processed and event published",
    };
    serde_json::to_string(&res).map_err(|_| "serialization failed")
}
