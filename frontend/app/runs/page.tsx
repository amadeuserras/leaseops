import { getLatestRun, listEmails } from '@/lib/api';
import { redirect } from 'next/navigation';

export const dynamic = 'force-dynamic';

/**
 * A run is always opened for a specific email, so `/runs` has nothing of its
 * own to show — it forwards to the most recently started run, or the newest
 * message if nothing has been run yet, or the inbox if empty.
 */
export default async function Page() {
  const latest = await getLatestRun();
  if (latest.email_id) {
    redirect(`/runs/${latest.email_id}`);
  }

  const emails = await listEmails();
  const newest = emails.items[0];
  redirect(newest ? `/runs/${newest.id}` : '/inbox');
}
