import { useEffect, useState } from 'react';

/** Existing mock profile selection and 250ms loading feedback. */
export function useProfileChart() {
    const [path, setPath] = useState('EURUSD / H1 / Volume profile');
    const [loading, setLoading] = useState(false);
    useEffect(() => { if (!loading)
        return; const timer = window.setTimeout(() => setLoading(false), 250); return () => window.clearTimeout(timer); }, [loading]);
    return { path, setPath, loading, setLoading };
}
