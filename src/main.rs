// \ mod
mod test;
// / mod

// \ extern
extern crate num_cpus;
extern crate tracing;
// / extern

// \ use
use tracing::info;
// / use

fn main() {
    tracing_subscriber::fmt::init();
    info!("main() {}", "start");
    // \ init
    let cpus = num_cpus::get();
    info!("num_cpus: {:?}", cpus);
    // / init
    info!("main() {}", "stop");
}
