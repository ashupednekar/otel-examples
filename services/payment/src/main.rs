use axum::{routing::post, Router};
use helpers::get_or_create_stream;
use opentelemetry::KeyValue;
use pay::handle_payment;
use state::AppState;
use std::{env, time::Duration};

use axum_tracing_opentelemetry::middleware::{OtelAxumLayer, OtelInResponseLayer};
use opentelemetry_otlp::{ExportConfig, SpanExporter, TonicConfig, WithExportConfig};
use opentelemetry_sdk::trace::TracerProvider;
use opentelemetry_sdk::{propagation::TraceContextPropagator, Resource};


mod data;
mod helpers;
mod pay;
mod state;

fn init_tracer() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();
    opentelemetry::global::set_text_map_propagator(TraceContextPropagator::new());

    let tracer_provider = opentelemetry_otlp::new_pipeline()
        .tracing()
        .with_exporter(
            opentelemetry_otlp::new_exporter()
                .tonic()
                .with_endpoint("http://localhost:4317")
                .with_timeout(Duration::from_secs(5))
        )
        .with_trace_config(opentelemetry_sdk::trace::Config::default().with_resource(
            Resource::new(vec![KeyValue::new("service.name", "payment")]),
        ))
        .install_batch(opentelemetry_sdk::runtime::Tokio)?;
    
    opentelemetry::global::set_tracer_provider(tracer_provider);
    Ok(())
}

#[tokio::main]
async fn main() {
    init_tracer().unwrap();
    let state = AppState::new().await;
    get_or_create_stream("events".to_string(), vec!["events.>".to_string()])
        .await
        .expect("stream creation failed");
    let app = Router::new()
        .route("/pay", post(handle_payment))
        .layer(OtelInResponseLayer::default())
        .layer(OtelAxumLayer::default())
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
