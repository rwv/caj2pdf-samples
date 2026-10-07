// SPDX-License-Identifier: MIT

// Copy this original generator to crates/caj2pdf-core/examples in a temporary
// current Rust worktree, then cargo run --locked -p caj2pdf-core --example
// hnb381_type3 -- /absolute/external/output. It imports only project-owned
// MIT fixture code; it never opens an external document or vendor library.
#![allow(dead_code)]
#[path = "../src/test_support/arith_encoder.rs"]
mod encoder;
fn mq_encoder() -> encoder::MqEncoder {
    encoder::MqEncoder::new(&caj2pdf_core::jbig2::mq::STANDARD_STATES.map(|s| {
        (s.qe, s.next_mps, s.next_lps, s.switch_mps)
    }))
}
mod fixture {
    include!("../tests/common/type3_fixture.rs");
}
fn main() {
    let directory = std::path::PathBuf::from(std::env::args_os().nth(1).expect("output directory"));
    std::fs::create_dir(&directory).unwrap();
    for name in ["white", "black", "left", "top", "checker"] {
        let (width, height) = (32, 24);
        let rows: Vec<Vec<bool>> = (0..height).map(|y| (0..width).map(|x| match name {
            "black" => true,
            "left" => x < 16,
            "top" => y < 12,
            "checker" => (x / 8 + y / 6) % 2 == 0,
            _ => false,
        }).collect()).collect();
        // The generic header is 20 bytes. Do not retain any old MQ data.
        let mut generic = fixture::generic_data(width, height)[..20].to_vec();
        let mut encoder = mq_encoder();
        encoder.template2(0, &rows);
        generic.extend(encoder.finish());
        let mut payload = fixture::dib(width, height).to_vec();
        payload.extend([
            fixture::segment(0, 48, &[], &fixture::page_data(width, height)),
            fixture::segment(1, 0, &[], &fixture::dictionary_data(0x0800)),
            fixture::segment(2, 0, &[1], &fixture::dictionary_data(0x1802)),
            fixture::segment(3, 6, &[2], &fixture::text_data(width, height, 0x10)),
            fixture::segment(4, 38, &[], &generic),
        ].concat());
        std::fs::write(directory.join(format!("{name}.bin")), payload).unwrap();
    }
}
