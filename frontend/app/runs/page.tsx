import { listEmails } from '@/lib/api';
import { redirect } from 'next/navigation';

export const dynamic = 'force-dynamic';

/**
 * A run is always opened for a specific email, so `/runs` has nothing of its
 * own to show — it forwards to the newest message, or to the inbox if empty.
 */
export default async function Page() {
  const data = await listEmails();
  const newest = data.items[0];
  redirect(newest ? `/runs/${newest.id}` : '/inbox');
}
