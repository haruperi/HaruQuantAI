/** Owner-local presentation/resource documents; no backend execution authority. */
export interface Dataset {
  id: string;
  source: string;
  symbol: string;
  timeframe: string;
  from: string;
  to: string;
  bars: number;
  quality: number;
  status: 'Ready' | 'Updating' | 'Error';
}

export interface Instrument {
  symbol: string;
  name: string;
  type: string;
  pointValue: number;
  spread: number;
  session: string;
  timezone: string;
}

/** Local validators and immutable document shapes, owned by this package. */
export const timezones: string[][] = [
  [
    "EETUS",
    "(EST+07) New York Trading hours, US DST"
  ],
  [
    "EET",
    "(UTC+02) European DST"
  ],
  [
    "Etc/UCT",
    "(UTC) Coordinated Universal Time"
  ],
  [
    "Europe/London",
    "(UTC) Dublin, Edinburgh, Lisbon, London"
  ],
  [
    "America/New_York",
    "(UTC-05) New York, US & Canada, EST"
  ],
  [
    "Etc/GMT+12",
    "(UTC-12) International Date Line West"
  ],
  [
    "Etc/GMT+11",
    "(UTC-11) Coordinated Universal Time-11"
  ],
  [
    "Pacific/Honolulu",
    "(UTC-10) Hawaii"
  ],
  [
    "America/Anchorage",
    "(UTC-09) Alaska"
  ],
  [
    "America/Los_Angeles",
    "(UTC-08) Baja California"
  ],
  [
    "America/Vancouver",
    "(UTC-08) Pacific Time (US & Canada)"
  ],
  [
    "America/Phoenix",
    "(UTC-07) Arizona"
  ],
  [
    "America/Chihuahua",
    "(UTC-07) Chihuahua, La Paz, Mazatlan"
  ],
  [
    "America/Denver",
    "(UTC-07) Mountain Time (US & Canada)"
  ],
  [
    "America/Chicago",
    "(UTC-06) Central America"
  ],
  [
    "America/Winnipeg",
    "(UTC-06) Central Time (US & Canada)"
  ],
  [
    "America/Mexico_City",
    "(UTC-06) Guadalajara, Mexico City, Monterrey"
  ],
  [
    "America/Regina",
    "(UTC-06) Saskatchewan"
  ],
  [
    "America/Bogota",
    "(UTC-05) Bogota, Lima, Quito, Rio Branco"
  ],
  [
    "America/New_York",
    "(UTC-05) Eastern Time (US & Canada)"
  ],
  [
    "America/Indiana/Indianapolis",
    "(UTC-05) Indiana (East)"
  ],
  [
    "America/Caracas",
    "(UTC-04:30) Caracas"
  ],
  [
    "America/Asuncion",
    "(UTC-04) Asuncion"
  ],
  [
    "America/Halifax",
    "(UTC-04) Atlantic Time (Canada)"
  ],
  [
    "America/Cuiaba",
    "(UTC-04) Cuiaba"
  ],
  [
    "America/Manaus",
    "(UTC-04) Georgetown, La Paz, Manaus, San Juan"
  ],
  [
    "America/Santiago",
    "(UTC-04) Santiago"
  ],
  [
    "America/St_Johns",
    "(UTC-03:30) Newfoundland"
  ],
  [
    "America/Sao_Paulo",
    "(UTC-03) Brasilia"
  ],
  [
    "America/Argentina/Buenos_Aires",
    "(UTC-03) Buenos Aires"
  ],
  [
    "America/Cayenne",
    "(UTC-03) Cayenne, Fortaleza"
  ],
  [
    "America/Cayenne",
    "(UTC-03) Greenland"
  ],
  [
    "America/Montevideo",
    "(UTC-03) Montevideo"
  ],
  [
    "America/Montevideo",
    "(UTC-03) Salvador"
  ],
  [
    "Etc/GMT+2",
    "(UTC-02) Coordinated Universal Time-02"
  ],
  [
    "Atlantic/Azores",
    "(UTC-01) Azores"
  ],
  [
    "Atlantic/Cape_Verde",
    "(UTC-01) Cabo Verde Is."
  ],
  [
    "Africa/Casablanca",
    "(UTC) Casablanca"
  ],
  [
    "Atlantic/Reykjavik",
    "(UTC) Monrovia, Reykjavik"
  ],
  [
    "Europe/Vienna",
    "(UTC+01) Amsterdam, Berlin, Bern, Rome, Stockholm, Vienna"
  ],
  [
    "Europe/Prague",
    "(UTC+01) Belgrade, Bratislava, Budapest, Ljubljana, Prague"
  ],
  [
    "Europe/Paris",
    "(UTC+01) Brussels, Copenhagen, Madrid, Paris"
  ],
  [
    "Europe/Warsaw",
    "(UTC+01) Sarajevo, Skopje, Warsaw, Zagreb"
  ],
  [
    "Africa/Brazzaville",
    "(UTC+01) West Central Africa"
  ],
  [
    "Africa/Windhoek",
    "(UTC+01) Windhoek"
  ],
  [
    "Asia/Amman",
    "(UTC+02) Amman"
  ],
  [
    "Europe/Athens",
    "(UTC+02) Athens, Bucharest"
  ],
  [
    "Asia/Beirut",
    "(UTC+02) Beirut"
  ],
  [
    "Africa/Cairo",
    "(UTC+02) Cairo"
  ],
  [
    "Asia/Damascus",
    "(UTC+02) Damascus"
  ],
  [
    "Africa/Harare",
    "(UTC+02) Harare, Pretoria"
  ],
  [
    "Europe/Helsinki",
    "(UTC+02) Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius"
  ],
  [
    "Europe/Istanbul",
    "(UTC+02) Istanbul"
  ],
  [
    "Asia/Jerusalem",
    "(UTC+02) Jerusalem"
  ],
  [
    "Europe/Kaliningrad",
    "(UTC+02) Kaliningrad (RTZ 1)"
  ],
  [
    "Africa/Tripoli",
    "(UTC+02) Tripoli"
  ],
  [
    "Asia/Baghdad",
    "(UTC+03) Baghdad"
  ],
  [
    "Asia/Kuwait",
    "(UTC+03) Kuwait, Riyadh"
  ],
  [
    "Europe/Minsk",
    "(UTC+03) Minsk"
  ],
  [
    "Europe/Moscow",
    "(UTC+03) Moscow, St. Petersburg, Volgograd (RTZ 2)"
  ],
  [
    "Europe/Kiev",
    "(UTC+03) Kiev"
  ],
  [
    "Africa/Nairobi",
    "(UTC+03) Nairobi"
  ],
  [
    "Asia/Tehran",
    "(UTC+03:30) Tehran"
  ],
  [
    "Asia/Muscat",
    "(UTC+04) Abu Dhabi, Muscat"
  ],
  [
    "Asia/Baku",
    "(UTC+04) Baku"
  ],
  [
    "Europe/Samara",
    "(UTC+04) Izhevsk, Samara (RTZ 3)"
  ],
  [
    "Asia/Tbilisi",
    "(UTC+04) Port Louis"
  ],
  [
    "Asia/Tbilisi",
    "(UTC+04) Tbilisi"
  ],
  [
    "Asia/Yerevan",
    "(UTC+04) Yerevan"
  ],
  [
    "Asia/Kabul",
    "(UTC+04:30) Kabul"
  ],
  [
    "Asia/Tashkent",
    "(UTC+05) Ashgabat, Tashkent"
  ],
  [
    "Asia/Yekaterinburg",
    "(UTC+05) Ekaterinburg (RTZ 4)"
  ],
  [
    "Asia/Karachi",
    "(UTC+05) Islamabad, Karachi"
  ],
  [
    "Asia/Kolkata",
    "(UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi"
  ],
  [
    "Asia/Kolkata",
    "(UTC+05:30) Sri Jayawardenepura"
  ],
  [
    "Asia/Kathmandu",
    "(UTC+05:45) Kathmandu"
  ],
  [
    "Asia/Dhaka",
    "(UTC+06) Astana"
  ],
  [
    "Asia/Dhaka",
    "(UTC+06) Dhaka"
  ],
  [
    "Asia/Novosibirsk",
    "(UTC+06) Novosibirsk (RTZ 5)"
  ],
  [
    "Asia/Rangoon",
    "(UTC+06:30) Yangon (Rangoon)"
  ],
  [
    "Asia/Bangkok",
    "(UTC+07) Bangkok, Hanoi, Jakarta"
  ],
  [
    "Asia/Krasnoyarsk",
    "(UTC+07) Krasnoyarsk (RTZ 6)"
  ],
  [
    "Asia/Urumqi",
    "(UTC+08) Beijing, Chongqing, Hong Kong, Urumqi"
  ],
  [
    "Asia/Irkutsk",
    "(UTC+08) Irkutsk (RTZ 7)"
  ],
  [
    "Asia/Kuala_Lumpur",
    "(UTC+08) Kuala Lumpur, Singapore"
  ],
  [
    "Australia/Perth",
    "(UTC+08) Perth"
  ],
  [
    "Asia/Taipei",
    "(UTC+08) Taipei"
  ],
  [
    "Asia/Ulaanbaatar",
    "(UTC+08) Ulaanbaatar"
  ],
  [
    "Asia/Tokyo",
    "(UTC+09) Osaka, Sapporo, Tokyo"
  ],
  [
    "Asia/Seoul",
    "(UTC+09) Seoul"
  ],
  [
    "Asia/Yakutsk",
    "(UTC+09) Yakutsk (RTZ 8)"
  ],
  [
    "Australia/Adelaide",
    "(UTC+09:30) Adelaide"
  ],
  [
    "Australia/Darwin",
    "(UTC+09:30) Darwin"
  ],
  [
    "Australia/Brisbane",
    "(UTC+10) Brisbane"
  ],
  [
    "Australia/Sydney",
    "(UTC+10) Canberra, Melbourne, Sydney"
  ],
  [
    "Pacific/Guam",
    "(UTC+10) Guam, Port Moresby"
  ],
  [
    "Australia/Hobart",
    "(UTC+10) Hobart"
  ],
  [
    "Asia/Magadan",
    "(UTC+10) Magadan"
  ],
  [
    "Asia/Vladivostok",
    "(UTC+10) Vladivostok, Magadan (RTZ 9)"
  ],
  [
    "Asia/Vladivostok",
    "(UTC+11) Chokurdakh (RTZ 10)"
  ],
  [
    "Pacific/Noumea",
    "(UTC+11) Solomon Is., New Caledonia"
  ],
  [
    "Asia/Anadyr",
    "(UTC+12) Anadyr, Petropavlovsk-Kamchatsky (RTZ 11)"
  ],
  [
    "Pacific/Auckland",
    "(UTC+12) Auckland, Wellington"
  ],
  [
    "Etc/GMT-12",
    "(UTC+12) Coordinated Universal Time+12"
  ],
  [
    "Pacific/Fiji",
    "(UTC+12) Fiji"
  ],
  [
    "Pacific/Tongatapu",
    "(UTC+13) Nuku'alofa"
  ],
  [
    "Etc/GMT-13",
    "(UTC+13) Samoa"
  ],
  [
    "Pacific/Kiritimati",
    "(UTC+14) Kiritimati Island"
  ],
  [
    "UTC",
    "UTC (application alias)"
  ]
];
