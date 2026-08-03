import { ApprovalsPage } from "@/components/approvals-page";
import { listApprovals } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Page() {
  const data = await listApprovals();
  return <ApprovalsPage data={data} />;
}
