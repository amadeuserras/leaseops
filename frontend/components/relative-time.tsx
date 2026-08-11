'use client';

import { fmtRelative } from '@/lib/format';
import { useEffect, useState } from 'react';

export function RelativeTime({ iso }: { iso: string | null }) {
  const [text, setText] = useState('');

  useEffect(() => {
    setText(fmtRelative(iso));
  }, [iso]);

  return <span>{text}</span>;
}
