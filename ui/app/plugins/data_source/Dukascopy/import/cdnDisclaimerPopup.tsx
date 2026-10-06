/** Download-local CDN disclaimer presentation within ImportPopup's modal. */
export function CdnDisclaimerPopup() {
  return (
    <section className="dukas-download-disclaimer">
      <h3>Disclaimer</h3>
      <p>
        In order to provide faster downloads for its clients HaruQuantAI offers pre-packaged
        Dukascopy data for some of the symbols on its own CDN servers.
      </p>
      <p>
        The data available on HaruQuantAI CDN were created from original Dukascopy data obtained
        from Dukascopy website. HaruQuantAI does not guarantee that the data prepared on its CDN
        servers exactly match Dukascopy data.
      </p>
      <p>
        The data are provided “AS IS”, “AS AVAILABLE”, “WITH ALL ITS FAULTS” and are offered without
        any covenants or any express, implied or statutory warranties including (without limitation
        and qualification) any warranties as to accuracy, functionality, performance,
        merchantability, quiet enjoyment, system integration, data accuracy or fitness for any
        particular purpose and any warranties arising from trade usage, course of dealing or course
        of performance.
      </p>
    </section>
  );
}
