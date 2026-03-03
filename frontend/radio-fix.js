// Working worldwide emergency radio stations
const WORLD_RADIO_STATIONS = [
    // GLOBAL NEWS (Most reliable)
    {
        name: "🌍 BBC World Service (Global News)",
        url: "https://stream.live.vc.bbcmedia.co.uk/bbc_world_service",
        country: "Global",
        language: "English",
        type: "News"
    },
    {
        name: "🇫🇷 France Inter - FIP (Eclectic Music)",
        url: "https://icecast.radiofrance.fr/fip-midfi.mp3",
        country: "France",
        language: "French",
        type: "Music/Culture"
    },
    {
        name: "🇩🇪 Deutschlandfunk (German News)",
        url: "https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3",
        country: "Germany",
        language: "German",
        type: "News"
    },
    {
        name: "🇯🇵 NHK World Radio (Japan)",
        url: "https://nhkworld.webcdn.stream.ne.jp/hls/live/2003459/nhkworld-r1/en/index.m3u8",
        country: "Japan",
        language: "English/Japanese",
        type: "News"
    },
    {
        name: "🇨🇦 CBC Radio One (Canada)",
        url: "https://cbcradiolive.akamaized.net/hls/live/2040959/ES_R1ETR/master.m3u8",
        country: "Canada",
        language: "English",
        type: "News"
    },
    {
        name: "🇯🇲 Kool 97 FM (Jamaica)",
        url: "https://ice.audionow.com:8000/Kool97FMLive.ogg",
        country: "Jamaica",
        language: "English",
        type: "Caribbean/Culture"
    },
    {
        name: "🇺🇸 KCRW (Los Angeles Public Radio)",
        url: "https://kcrw.streamguys1.com/kcrw_128k_mp3_aac",
        country: "USA",
        language: "English",
        type: "Public Radio"
    },
    {
        name: "🇺🇸 WFMU (Freeform Radio)",
        url: "https://stream0.wfmu.org/freeform-128",
        country: "USA",
        language: "English",
        type: "Eclectic"
    },
    {
        name: "🇦🇺 ABC News Radio (Australia)",
        url: "https://abcradiolivehls-lh.akamaihd.net/i/news_1@319354/index_128_a-p.m3u8",
        country: "Australia",
        language: "English",
        type: "News"
    },
    {
        name: "🇳🇿 Radio New Zealand National",
        url: "https://streaming.radionz.co.nz/national-mp3",
        country: "New Zealand",
        language: "English",
        type: "News/Culture"
    },
    {
        name: "🇦🇹 Radio Österreich 1 (Austria)",
        url: "https://orf-live.ors-shoutcast.at/oe1-q2a",
        country: "Austria",
        language: "German",
        type: "Classical/News"
    },
    {
        name: "🇮🇹 RAI Radio 1 (Italy)",
        url: "https://icestreaming.rai.it/1.mp3",
        country: "Italy",
        language: "Italian",
        type: "News"
    },
    {
        name: "🇪🇸 RNE Radio Nacional (Spain)",
        url: "https://rtve-edge-3.b.cdn.dazn.com/live/rtve/rtve-rne5/stream_350.m3u8",
        country: "Spain",
        language: "Spanish",
        type: "News"
    },
    {
        name: "🇸🇪 SR P1 (Sweden)",
        url: "https://http-live.sr.se/p1-mp3-192",
        country: "Sweden",
        language: "Swedish",
        type: "News"
    },
    {
        name: "🇨🇭 Radio Swiss Classic",
        url: "https://stream.srg-ssr.ch/rsc_fr/mp3_128",
        country: "Switzerland",
        language: "Multilingual",
        type: "Classical"
    },
    {
        name: "🇨🇭 Radio Swiss Jazz",
        url: "https://stream.srg-ssr.ch/rsj_fr/mp3_128",
        country: "Switzerland",
        language: "Multilingual",
        type: "Jazz"
    },
    {
        name: "🇮🇪 RTÉ Radio 1 (Ireland)",
        url: "https://icecast.rte.ie/rte1",
        country: "Ireland",
        language: "English",
        type: "News"
    },
    {
        name: "🇧🇪 VRT Radio 1 (Belgium)",
        url: "https://icecast.vrtcdn.be/radio1-high.mp3",
        country: "Belgium",
        language: "Dutch",
        type: "News"
    },
    {
        name: "🇳🇱 NPO Radio 1 (Netherlands)",
        url: "https://icecast.omroep.nl/radio1-bb-mp3",
        country: "Netherlands",
        language: "Dutch",
        type: "News"
    },
    {
        name: "🇳🇴 NRK P1 (Norway)",
        url: "https://lyd.nrk.no/nrk_radio_p1_ostlandssendingen_mp3_h",
        country: "Norway",
        language: "Norwegian",
        type: "News"
    },
    {
        name: "🇩🇰 DR P1 (Denmark)",
        url: "https://drliveradio.akamaized.net/hls/live/2022411/p1/master.m3u8",
        country: "Denmark",
        language: "Danish",
        type: "News"
    },
    {
        name: "🇫🇮 YLE Radio 1 (Finland)",
        url: "https://yleradiolive.akamaized.net/hls/live/2027665/in-YleRadio1/master.m3u8",
        country: "Finland",
        language: "Finnish",
        type: "Culture"
    },
    {
        name: "🇮🇸 RÚV Rás 1 (Iceland)",
        url: "https://ruv-ras1-live-hls.secure.footprint.net/hls-live/ruv-ras1/ruv-ras1.m3u8",
        country: "Iceland",
        language: "Icelandic",
        type: "News/Culture"
    },
    {
        name: "🇵🇹 Antena 1 (Portugal)",
        url: "https://radioip.rtp.pt/liveradio/antena180a/playlist.m3u8",
        country: "Portugal",
        language: "Portuguese",
        type: "News"
    },
    {
        name: "🇬🇷 ERT Proto (Greece)",
        url: "https://radiostreaming.ert.gr/ert-proto",
        country: "Greece",
        language: "Greek",
        type: "News"
    },
    {
        name: "🇹🇷 TRT Radyo 1 (Turkey)",
        url: "https://trtcanli.mediatriple.net/trt_1.m3u8",
        country: "Turkey",
        language: "Turkish",
        type: "News"
    },
    {
        name: "🇮🇱 Kan Tarbut (Israel)",
        url: "https://kanlivep2event-i.akamaihd.net/hls/live/749626/749626/playlist.m3u8",
        country: "Israel",
        language: "Hebrew",
        type: "Culture"
    },
    {
        name: "🇿🇦 SAFM (South Africa)",
        url: "https://playerservices.streamtheworld.com/api/livestream-redirect/SAFM.mp3",
        country: "South Africa",
        language: "English",
        type: "News"
    },
    {
        name: "🇦🇪 Dubai Eye (UAE)",
        url: "https://stream.radio.co/s6f50eeeff/listen",
        country: "UAE",
        language: "English",
        type: "News"
    },
    {
        name: "🇸🇬 Symphony 924 (Singapore)",
        url: "https://mediacorp.streampredict.com/symphony924/sync/stream.mp3",
        country: "Singapore",
        language: "English",
        type: "Classical"
    }
];
