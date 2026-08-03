import { InboxPage } from "@/components/inbox-page";
import { listEmails } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Page() {
  const data = await listEmails();
  return <InboxPage data={data} />;
}
