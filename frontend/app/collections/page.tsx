"use client";

import { useState } from "react";
import CollectionsQueueTable from "./_components/CollectionsQueueTable";
import CaseDrawer from "./_components/CaseDrawer";

export default function CollectionsPage() {
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);

  return (
    <div className="p-6">
      <CollectionsQueueTable onSelectCase={setSelectedCaseId} />
      <CaseDrawer caseId={selectedCaseId} onClose={() => setSelectedCaseId(null)} />
    </div>
  );
}
