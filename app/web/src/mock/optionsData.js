export const generateOptionsGrid = (underlyingPrice = 6243.75) => {
  const baseStrike = Math.round(underlyingPrice / 25) * 25;
  const strikes = [];

  for (let i = -10; i <= 10; i++) {
    const strike = baseStrike + i * 25;
    const isATM = i === 0;

    // Call pricing model mockup
    const callIntrinsic = Math.max(0, underlyingPrice - strike);
    const callExtrinsic = Math.max(5, 150 - Math.abs(i) * 12);
    const callPrice = parseFloat((callIntrinsic + callExtrinsic).toFixed(2));
    const callBid = parseFloat((callPrice - 0.5).toFixed(2));
    const callOffer = parseFloat((callPrice + 0.5).toFixed(2));

    // Put pricing model mockup
    const putIntrinsic = Math.max(0, strike - underlyingPrice);
    const putExtrinsic = Math.max(5, 150 - Math.abs(i) * 12);
    const putPrice = parseFloat((putIntrinsic + putExtrinsic).toFixed(2));
    const putBid = parseFloat((putPrice - 0.5).toFixed(2));
    const putOffer = parseFloat((putPrice + 0.5).toFixed(2));

    strikes.push({
      strike,
      isATM,
      calls: {
        low: parseFloat((callPrice * 0.85).toFixed(2)),
        high: parseFloat((callPrice * 1.15).toFixed(2)),
        prior: parseFloat((callPrice * 0.95).toFixed(2)),
        change: parseFloat(((Math.random() - 0.4) * 10).toFixed(2)),
        last: callPrice,
        qty: Math.floor(Math.random() * 500) + 10,
        bid: callBid,
        offer: callOffer
      },
      puts: {
        bid: putBid,
        offer: putOffer,
        qty: Math.floor(Math.random() * 500) + 10,
        last: putPrice,
        change: parseFloat(((Math.random() - 0.6) * 10).toFixed(2)),
        prior: parseFloat((putPrice * 0.95).toFixed(2)),
        low: parseFloat((putPrice * 0.85).toFixed(2)),
        high: parseFloat((putPrice * 1.15).toFixed(2))
      }
    });
  }

  return strikes;
};
