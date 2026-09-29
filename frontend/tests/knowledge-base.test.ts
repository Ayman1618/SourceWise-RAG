import {
  KNOWLEDGE_DOCUMENTS,
  ALL_PRODUCTS,
  ALL_SOURCE_TYPES,
  ALL_DEPARTMENTS,
  ALL_VERSIONS,
  searchKnowledgeBase,
  getKnowledgeDocumentById,
} from "../lib/knowledge-data";

function runTestSuite() {
  console.log("=================================================");
  console.log("Starting SourceWise Knowledge Base Test Suite...");
  console.log("=================================================\n");

  let passed = 0;
  let total = 0;

  function assert(condition: boolean, testName: string) {
    total++;
    if (condition) {
      console.log(`✓ Test ${total} Passed: ${testName}`);
      passed++;
    } else {
      console.error(`✗ Test ${total} Failed: ${testName}`);
      process.exitCode = 1;
    }
  }

  // Test 1: Knowledge Documents Catalog Count & Access Level Verification
  console.log("Test 1: Verifying Knowledge Base Documents Catalog...");
  assert(KNOWLEDGE_DOCUMENTS.length === 5, "Catalog contains 5 core knowledge documents");
  assert(
    KNOWLEDGE_DOCUMENTS.every((doc) => Boolean(doc.id && doc.title && doc.accessLevel)),
    "All catalog documents possess valid ID, title, and accessLevel properties"
  );

  // Test 2: Search by Document ID
  console.log("\nTest 2: Searching Knowledge Base by Document ID...");
  const searchById = searchKnowledgeBase("DOC-2024-881");
  assert(
    searchById.length === 1 && searchById[0].id === "DOC-2024-881",
    "Search by exact Document ID 'DOC-2024-881' returns correct document"
  );

  // Test 3: Search by Title & Keyword
  console.log("\nTest 3: Searching Knowledge Base by Title & Keyword...");
  const searchByTitle = searchKnowledgeBase("troubleshooting");
  assert(
    searchByTitle.length >= 1 && searchByTitle[0].title.includes("Troubleshooting"),
    "Search by title keyword 'troubleshooting' returns relevant document"
  );

  // Test 4: Search by Department
  console.log("\nTest 4: Searching Knowledge Base by Department...");
  const searchByDept = searchKnowledgeBase("Security Architecture");
  assert(
    searchByDept.length >= 1 && searchByDept[0].department === "Security Architecture",
    "Search by department 'Security Architecture' returns matching specification"
  );

  // Test 5: Filtering by Product
  console.log("\nTest 5: Filtering Knowledge Base by Product...");
  const filterByProduct = searchKnowledgeBase("", "Security Standards");
  assert(
    filterByProduct.length === 1 && filterByProduct[0].product === "Security Standards",
    "Filtering by Product 'Security Standards' returns expected document"
  );

  // Test 6: Filtering by Source Type
  console.log("\nTest 6: Filtering Knowledge Base by Source Type...");
  const filterByType = searchKnowledgeBase("", "", "Operations Runbook");
  assert(
    filterByType.length === 1 && filterByType[0].sourceType === "Operations Runbook",
    "Filtering by Source Type 'Operations Runbook' returns runbook document"
  );

  // Test 7: Multi-Filter Combination (Product + Department + Version)
  console.log("\nTest 7: Filtering with Combined Metadata Criteria...");
  const multiFilter = searchKnowledgeBase("", "Authentication & Access", "", "Support Operations", "v2.1");
  assert(
    multiFilter.length === 1 && multiFilter[0].id === "DOC-2024-881",
    "Multi-filter combination (Product, Department, Version) isolates correct document"
  );

  // Test 8: Document Retrieval by ID & Slug
  console.log("\nTest 8: Document Lookup by ID and Slug...");
  const docById = getKnowledgeDocumentById("DOC-2024-412");
  const docBySlug = getKnowledgeDocumentById("product-authentication-guide");
  assert(
    docById?.id === "DOC-2024-412" && docBySlug?.id === "DOC-2024-412",
    "getKnowledgeDocumentById resolves document accurately via ID or Slug"
  );

  // Test 9: Unknown Document ID Handling
  console.log("\nTest 9: Handling Unknown Document Identifier...");
  const unknownDoc = getKnowledgeDocumentById("DOC-INVALID-9999");
  assert(
    unknownDoc === undefined,
    "getKnowledgeDocumentById returns undefined for unknown document identifier"
  );

  // Test 10: Empty Search Results
  console.log("\nTest 10: Verifying Empty Search Results...");
  const emptyResults = searchKnowledgeBase("nonexistent_query_xyz_12345");
  assert(
    emptyResults.length === 0,
    "searchKnowledgeBase returns empty array for non-matching queries"
  );

  console.log("\n=========================================");
  console.log(`RESULTS: ${passed} / ${total} TESTS PASSED`);
  console.log("=========================================\n");

  if (passed !== total) {
    process.exit(1);
  }
}

runTestSuite();
