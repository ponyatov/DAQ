// \ mod
mod test;
// / mod

// \ extern
extern crate num_cpus;
extern crate tracing;
// / extern

// \ use
use tracing::{info, instrument};
// / use

#[instrument]
fn main() {
    tracing_subscriber::fmt::init();
    info!("start");
    // \ init
    cpu();
    // / init
    info!("stop");
}

// \ cpu
#[derive(Debug)]
struct CPU {
    cores: u8,
    vendor: String,
    brand: String,
    serial: u128,
}

impl CPU {
    pub fn new() -> Self {
        let cpuid = raw_cpuid::CpuId::new();
        CPU {
            cores: num_cpus::get() as u8,
            vendor: String::from(cpuid.get_vendor_info().unwrap().as_str()),
            brand: String::from(cpuid.get_processor_brand_string().unwrap().as_str()),
            serial: cpuid.get_processor_serial().unwrap().serial_all(),
        }
    }
}

#[instrument]
fn cpu() {
    info!("{:?}", CPU::new());
}
// / cpu
