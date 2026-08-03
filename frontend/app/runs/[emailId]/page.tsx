import { RunsPage } from '@/components/runs-page';
import { getRun } from '@/lib/api';

export const dynamic = 'force-dynamic';

export default async function Page({ params }: { params: Promise<{ emailId: string }> }) {
  const { emailId } = await params;
  const data = await getRun(emailId);
  return <RunsPage data={data} />;
}
