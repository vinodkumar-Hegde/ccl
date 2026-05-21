import api from "./api";

export async function fullProcessCase(data) {
  const response = await api.post(
    "/full-process/case",
    data,
    {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    }
  );

  return response.data;
}

export async function getCases() {
  const response = await api.get(
    `/cases/?t=${Date.now()}`
  );

  return response.data;
}

export async function getPublishedCases() {
  const response = await api.get(
    `/cases/published?t=${Date.now()}`
  );

  return response.data;
}

export async function getCase(caseId) {
  const response = await api.get(
    `/cases/${caseId}?t=${Date.now()}`
  );

  return response.data;
}

export async function getCaseFiles(caseId) {
  const response = await api.get(
    `/case-files/${caseId}?t=${Date.now()}`
  );

  return response.data;
}

export async function updateCaseStatus(caseId, status) {
  const response = await api.patch(
    `/cases/${caseId}/status?status=${status}`
  );

  return response.data;
}

export async function deleteCase(caseId) {
  const response = await api.delete(
    `/cases/${caseId}`
  );

  return response.data;
}

export async function updateCaseAI(caseId, payload) {
  const response = await api.put(
    `/case-ai/${caseId}`,
    payload
  );

  return response.data;
}
