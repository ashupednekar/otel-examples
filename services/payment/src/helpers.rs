use async_nats::jetstream::{
    self,
    stream::{Config, Stream},
    Context,
};
use async_nats::{
    connect_with_options, jetstream::stream::RetentionPolicy, Client, ConnectOptions,
};
use std::{collections::HashSet, env};

pub async fn get_nats_connection() -> Result<Client, async_nats::Error> {
    let broker_url = env::var("NATS_URL").unwrap_or("localhost:4222".to_string());
    let client = connect_with_options(broker_url, ConnectOptions::new().name("payment"))
        .await
        .unwrap();
    Ok(client)
}

pub async fn get_nats_jetstream_context() -> Result<Context, async_nats::Error> {
    let client = get_nats_connection().await?;
    let jetstream_ctx = jetstream::new(client);
    Ok(jetstream_ctx)
}

pub async fn update_stream(stream: String, subjects: Vec<String>) -> Result<(), async_nats::Error> {
    let context = get_nats_jetstream_context().await?;
    let config = jetstream::stream::Config {
        name: stream.clone(),
        subjects,
        retention: jetstream::stream::RetentionPolicy::WorkQueue,
        ..Default::default()
    };
    match context.update_stream(config.clone()).await {
        Ok(_) => {
            println!("stream updated successfully")
        }
        Err(e) => {
            println!("stream couldn't be updated because {}", e);
        }
    };
    Ok(())
}

pub async fn get_or_create_stream(
    stream: String,
    subjects: Vec<String>,
) -> Result<Stream, async_nats::Error> {
    let context = get_nats_jetstream_context().await?;
    let config = Config {
        name: stream.clone(),
        retention: RetentionPolicy::WorkQueue,
        ..Default::default()
    };
    let js = context.get_or_create_stream(config.clone()).await.unwrap();
    let mut all_subjects: HashSet<String> = subjects.into_iter().collect();
    let current_subjects = js.cached_info().clone().config.subjects;
    all_subjects.extend(current_subjects.clone());
    all_subjects.insert(format!("internal.{}", stream.clone()));
    let subs: Vec<String> = all_subjects.into_iter().collect();
    update_stream(stream, subs).await.unwrap();
    Ok(js)
}
