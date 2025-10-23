# Analysis of Issues Related to Load Balancers, Cloud Armor and PSC in Terraform Provider Google

Report date: 2025-09-08 14:23:51

## Executive Summary

This report presents OPEN and AVAILABLE issues in the Terraform Provider Google repository 
related to the specific services requested by the client:

- **Load Balancers**
- **Cloud Armor**
- **Private Service Connect (PSC)**

A total of **142** open and available issues related to these services were identified.

## Distribution by Service

- **Private Service Connect (PSC)**: 94 issues (Average confidence: 78.5%)
- **Load Balancers**: 88 issues (Average confidence: 79.9%)
- **Cloud Armor**: 32 issues (Average confidence: 83.1%)

## Available Issues by Category

The following issues are currently OPEN and AVAILABLE for contribution (not claimed by other contributors):

### Private Service Connect (PSC) (66 issues)

1. 🟢 **[#10538](https://github.com/hashicorp/terraform-provider-google/issues/10538)** - google_service_networking_connection creates the peering connections but not all routes 🐞 (created on 2021-11-10, confidence: 85.0%)
2. 🟢 **[#11862](https://github.com/hashicorp/terraform-provider-google/issues/11862)** - create instance terraform gcp with shared vpc 🐞 (created on 2022-06-10, confidence: 85.0%)
3. 🟢 **[#16016](https://github.com/hashicorp/terraform-provider-google/issues/16016)** - google_sql_database_instance and psc 🐞 (created on 2023-09-27, confidence: 85.0%)
4. 🟢 **[#17153](https://github.com/hashicorp/terraform-provider-google/issues/17153)** - Error Updating google_compute_service_attachment Resource with connection_preference Set to `ACCEPT_AUTOMATIC` 🐞 (created on 2024-01-31, confidence: 85.0%)
5. 🟢 **[#18280](https://github.com/hashicorp/terraform-provider-google/issues/18280)** - Impossible to create AlloyDB instance with PSC enabled 🐞 (created on 2024-05-30, confidence: 85.0%)
6. 🟢 **[#19779](https://github.com/hashicorp/terraform-provider-google/issues/19779)** - google_compute_network_peering_routes_config returns Error 400: Required field '' not specified, required 🐞 (created on 2024-10-08, confidence: 85.0%)
7. 🟢 **[#20398](https://github.com/hashicorp/terraform-provider-google/issues/20398)** - `google_service_networking_connection` always detects changes if `reserved_peering_ranges` has multiple entries and is not a static list  🐞 (created on 2024-11-19, confidence: 85.0%)
8. 🟢 **[#20448](https://github.com/hashicorp/terraform-provider-google/issues/20448)** - `google_container_cluster` does not support using GKE-managed Services range in a Shared VPC setup 🐞 (created on 2024-11-22, confidence: 85.0%)
9. 🟢 **[#21849](https://github.com/hashicorp/terraform-provider-google/issues/21849)** - `google_compute_network_peering_routes_config`: Network Peering Routes Config Gke doesn't work in docs 🐞 (created on 2025-03-13, confidence: 85.0%)
10. 🟢 **[#8768](https://github.com/hashicorp/terraform-provider-google/issues/8768)** - Terraform doesn't show meaningful error-details on http 400 (google_cloudfunctions_function) 🐞 (created on 2021-03-25, confidence: 75.0%)
11. 🟢 **[#10198](https://github.com/hashicorp/terraform-provider-google/issues/10198)** - disabling master authorized network after it is enabled 🐞 (created on 2021-09-30, confidence: 75.0%)
12. 🟢 **[#10540](https://github.com/hashicorp/terraform-provider-google/issues/10540)** - Resource id needs to be "url-defied" 🐞 (created on 2021-11-10, confidence: 75.0%)
13. 🟢 **[#11116](https://github.com/hashicorp/terraform-provider-google/issues/11116)** - On destroy throws Error when reading or editing ServiceNetworkingConnection: no peering for network 🐞 (created on 2022-02-15, confidence: 75.0%)
14. 🟢 **[#11144](https://github.com/hashicorp/terraform-provider-google/issues/11144)** - google-beta v4.11.0crashes on google_container_cluster 🐞 (created on 2022-02-22, confidence: 75.0%)
15. 🟢 **[#16352](https://github.com/hashicorp/terraform-provider-google/issues/16352)** - google_datastream_private_connection resource generates random display_name and doesn't give value in output attribute 🐞 (created on 2023-10-25, confidence: 75.0%)
16. 🟢 **[#17731](https://github.com/hashicorp/terraform-provider-google/issues/17731)** - Unable to Create Apigee X Subscription Org 🐞 (created on 2024-03-29, confidence: 75.0%)
17. 🟢 **[#18666](https://github.com/hashicorp/terraform-provider-google/issues/18666)** - google_compute_shared_vpc_service_project: resource is abandoned on destroy if project number is used on create 🐞 (created on 2024-07-08, confidence: 75.0%)
18. 🟢 **[#18667](https://github.com/hashicorp/terraform-provider-google/issues/18667)** - `google_service_networking_vpc_service_controls` Doesn't successfully apply enable/disable 🐞 (created on 2024-07-08, confidence: 75.0%)
19. 🟢 **[#19474](https://github.com/hashicorp/terraform-provider-google/issues/19474)** - 5.X Performance Issues for resource_access_context_manager_service_perimeter 🐞 (created on 2024-09-13, confidence: 75.0%)
20. 🟢 **[#20101](https://github.com/hashicorp/terraform-provider-google/issues/20101)** - Missing `update_mask` field in `google_memorystore_instance` resource 🐞 (created on 2024-10-30, confidence: 75.0%)
21. 🟢 **[#21026](https://github.com/hashicorp/terraform-provider-google/issues/21026)** - `google_vertex_ai_endpoint_iam_policy` doesn't expect the argument "region" 🐞 (created on 2025-01-23, confidence: 75.0%)
22. 🟢 **[#21068](https://github.com/hashicorp/terraform-provider-google/issues/21068)** - AlloyDB instance state in Terraform returns "ready" significantly earlier than GCP instance state is ready 🐞 (created on 2025-01-28, confidence: 75.0%)
23. 🟢 **[#22030](https://github.com/hashicorp/terraform-provider-google/issues/22030)** - google_sql_database_instance Edition defaults incorrectly and shows drift and an error 🐞 (created on 2025-03-24, confidence: 75.0%)
24. 🟢 **[#22206](https://github.com/hashicorp/terraform-provider-google/issues/22206)** - panic: runtime error: index out of range [-1] 🐞 (created on 2025-04-02, confidence: 75.0%)
25. 🟢 **[#23602](https://github.com/hashicorp/terraform-provider-google/issues/23602)** - missing google_gke_backup_backup_plan backup_schedule.rpo_config.exclusion_windows.start_time when set to 0 🐞 (created on 2025-07-14, confidence: 75.0%)
26. 🟢 **[#8396](https://github.com/hashicorp/terraform-provider-google/issues/8396)** - google_service_networking_connection has no options for importing/exporting custom routes (created on 2021-02-05, confidence: 85.0%)
27. 🟢 **[#9559](https://github.com/hashicorp/terraform-provider-google/issues/9559)** - Support for export of routes w/ public IPs in google_compute_network_peering_routes_config (created on 2021-07-14, confidence: 85.0%)
28. 🟢 **[#10094](https://github.com/hashicorp/terraform-provider-google/issues/10094)** - Allow google_compute_network_peering to accept google_compute_network.id format in network field (created on 2021-09-17, confidence: 85.0%)
29. 🟢 **[#11667](https://github.com/hashicorp/terraform-provider-google/issues/11667)** - Documentation issue: Serverless VPC Access for shared VPC (created on 2022-05-09, confidence: 85.0%)
30. 🟢 **[#12042](https://github.com/hashicorp/terraform-provider-google/issues/12042)** - google_service_networking_connection: does not have options for export subet routes with public ip (created on 2022-07-07, confidence: 85.0%)
31. 🟢 **[#14653](https://github.com/hashicorp/terraform-provider-google/issues/14653)** - New Data Source `compute_network_peering_routes` (created on 2023-05-18, confidence: 85.0%)
32. 🟢 **[#15864](https://github.com/hashicorp/terraform-provider-google/issues/15864)** - Investigate cleaning up TestAccSqlDatabaseInstance_withPSCEnabled tests (created on 2023-09-15, confidence: 85.0%)
33. 🟢 **[#16735](https://github.com/hashicorp/terraform-provider-google/issues/16735)** - google_service_networking_connection support append to reserved_peering_ranges  (created on 2023-12-08, confidence: 85.0%)
34. 🟢 **[#17116](https://github.com/hashicorp/terraform-provider-google/issues/17116)** - Support for networks in PSC consumer accept lists (created on 2024-01-26, confidence: 85.0%)
35. 🟢 **[#17298](https://github.com/hashicorp/terraform-provider-google/issues/17298)** - Allow attaching access levels to the already created service perimeters (created on 2024-02-16, confidence: 85.0%)
36. 🟢 **[#18339](https://github.com/hashicorp/terraform-provider-google/issues/18339)** - In Data Fusion resource, add network config fields for Private Service Connect as existing in API. (created on 2024-06-06, confidence: 85.0%)
37. 🟢 **[#18783](https://github.com/hashicorp/terraform-provider-google/issues/18783)** - Data sources for Access Context Manager (VPC Service Controls) Supported Services (created on 2024-07-18, confidence: 85.0%)
38. 🟢 **[#20846](https://github.com/hashicorp/terraform-provider-google/issues/20846)** - Documentation enhancement Filestore Shared VPC and Private Service Access (created on 2025-01-08, confidence: 85.0%)
39. 🟢 **[#22169](https://github.com/hashicorp/terraform-provider-google/issues/22169)** - Creation of PSC Service Attachment Failing for Secure Web Proxy (created on 2025-03-31, confidence: 85.0%)
40. 🟢 **[#3490](https://github.com/hashicorp/terraform-provider-google/issues/3490)** - List usable subnetworks (created on 2019-04-25, confidence: 75.0%)
41. 🟢 **[#8560](https://github.com/hashicorp/terraform-provider-google/issues/8560)** - Reservation scheduling option to google_tpu_node (created on 2021-02-25, confidence: 75.0%)
42. 🟢 **[#9629](https://github.com/hashicorp/terraform-provider-google/issues/9629)** - Update documentation for Service Network Connection (created on 2021-07-25, confidence: 75.0%)
43. 🟢 **[#16176](https://github.com/hashicorp/terraform-provider-google/issues/16176)** - google_sql_database_instance missing attributes in docs  (created on 2023-10-09, confidence: 75.0%)
44. 🟢 **[#16365](https://github.com/hashicorp/terraform-provider-google/issues/16365)** - "google_access_context_manager_access_level" "members" condition should include groups (created on 2023-10-25, confidence: 75.0%)
45. 🟢 **[#16450](https://github.com/hashicorp/terraform-provider-google/issues/16450)** - Documentation improvements for google_sql_database_instance (created on 2023-11-06, confidence: 75.0%)
46. 🟢 **[#16894](https://github.com/hashicorp/terraform-provider-google/issues/16894)** - Error creating Database: googleapi: Error 403: The client is not authorized to make this request., notAuthorized (created on 2024-01-03, confidence: 75.0%)
47. 🟢 **[#17846](https://github.com/hashicorp/terraform-provider-google/issues/17846)** - Separate resource for adding additional consumers to an existing service attachement (created on 2024-04-15, confidence: 75.0%)
48. 🟢 **[#18945](https://github.com/hashicorp/terraform-provider-google/issues/18945)** - google_access_context_manager_service_perimeter ingress_to should allow multiple source resources. (created on 2024-08-01, confidence: 75.0%)
49. 🟢 **[#19501](https://github.com/hashicorp/terraform-provider-google/issues/19501)** - I have multiple /28s and google_apigee_organization and google_apigee_instance won't let me choose which one to use for support range (created on 2024-09-17, confidence: 75.0%)
50. 🟢 **[#19529](https://github.com/hashicorp/terraform-provider-google/issues/19529)** - Enable to recursively get a list of all projects under a folder (created on 2024-09-19, confidence: 75.0%)
51. 🟢 **[#19936](https://github.com/hashicorp/terraform-provider-google/issues/19936)** - Add PEER_MIGRATION purpose to compute_subnetwork resource  (created on 2024-10-21, confidence: 75.0%)
52. 🟢 **[#19937](https://github.com/hashicorp/terraform-provider-google/issues/19937)** - Allow Subnet with purpose set to PEER_MIGRATION to be updated with purpose set to PRIVATE. (created on 2024-10-21, confidence: 75.0%)
53. 🟢 **[#20571](https://github.com/hashicorp/terraform-provider-google/issues/20571)** - Failing test(s): TestAccCloudfunctions2function_cloudfunctions2BasicBuilderExample (created on 2024-12-03, confidence: 75.0%)
54. 🟢 **[#20802](https://github.com/hashicorp/terraform-provider-google/issues/20802)** - Failing test(s): TestAccAlloydbCluster_withPrivateServiceConnect and more (created on 2024-12-30, confidence: 75.0%)
55. 🟢 **[#21181](https://github.com/hashicorp/terraform-provider-google/issues/21181)** - Failing test(s): TestAccApigeeEndpointAttachment_apigeeEndpointAttachmentBasicTestExample (created on 2025-01-31, confidence: 75.0%)
56. 🟢 **[#21182](https://github.com/hashicorp/terraform-provider-google/issues/21182)** - Failing test(s): TestAccApigeeInstance_apigeeInstanceBasicTestExample (created on 2025-01-31, confidence: 75.0%)
57. 🟢 **[#21373](https://github.com/hashicorp/terraform-provider-google/issues/21373)** - Failing test(s): TestAccApigeeOrganization_update (created on 2025-02-12, confidence: 75.0%)
58. 🟢 **[#21445](https://github.com/hashicorp/terraform-provider-google/issues/21445)** - Failing test(s): TestAccApigeeEnvReferences_apigeeEnvironmentReferenceTest_Update (created on 2025-02-17, confidence: 75.0%)
59. 🟢 **[#21768](https://github.com/hashicorp/terraform-provider-google/issues/21768)** - Failing test(s): TestAccApigeeInstance_apigeeInstanceIpRangeTestExample (created on 2025-03-09, confidence: 75.0%)
60. 🟢 **[#21771](https://github.com/hashicorp/terraform-provider-google/issues/21771)** - Failing test(s): TestAccApigeeEnvironment_apigeeEnvironmentBasicDeploymentApiproxyTypeTestExample (created on 2025-03-10, confidence: 75.0%)
61. 🟢 **[#21883](https://github.com/hashicorp/terraform-provider-google/issues/21883)** - Failing test(s): TestAccApigeeSharedflowDeployment_apigeeSharedflowDeploymentTestExample (created on 2025-03-16, confidence: 75.0%)
62. 🟢 **[#21964](https://github.com/hashicorp/terraform-provider-google/issues/21964)** - Failing test(s): TestAccApigeeEnvironmentIamBindingGenerated (created on 2025-03-21, confidence: 75.0%)
63. 🟢 **[#22233](https://github.com/hashicorp/terraform-provider-google/issues/22233)** - Missing encryptionSpec (KMS CMEK) in google_vertex_ai_index_endpoint (created on 2025-04-04, confidence: 75.0%)
64. 🟢 **[#22290](https://github.com/hashicorp/terraform-provider-google/issues/22290)** - Support IP address creation based on a designated subprefix (created on 2025-04-10, confidence: 75.0%)
65. 🟢 **[#23634](https://github.com/hashicorp/terraform-provider-google/issues/23634)** - Implement google_compute_network_attachment_iam_policy (created on 2025-07-17, confidence: 75.0%)
66. 🟢 **[#23796](https://github.com/hashicorp/terraform-provider-google/issues/23796)** - Add Apigee Spaces resource to set fine-grained permission on API proxies, etc (created on 2025-07-30, confidence: 75.0%)

### Load Balancers (55 issues)

1. 🟢 **[#9010](https://github.com/hashicorp/terraform-provider-google/issues/9010)** - Updating google_compute_forwarding_rule causes conflict error 🐞 (created on 2021-04-27, confidence: 85.0%)
2. 🟢 **[#11657](https://github.com/hashicorp/terraform-provider-google/issues/11657)** - Terraform created internet network endpoint group does not work with load balancer 🐞 (created on 2022-05-06, confidence: 85.0%)
3. 🟢 **[#15731](https://github.com/hashicorp/terraform-provider-google/issues/15731)** - Not able to attach cloud armor edge policy to gcp load balancer backend bucket 🐞 (created on 2023-09-06, confidence: 85.0%)
4. 🟢 **[#16359](https://github.com/hashicorp/terraform-provider-google/issues/16359)** - Error when deleting InstanceGroup AND removing from ILB Backend 🐞 (created on 2023-10-25, confidence: 85.0%)
5. 🟢 **[#16870](https://github.com/hashicorp/terraform-provider-google/issues/16870)** - Changing PSC Consumer Endpoint IP Address doesn't trigger required forwarding rule re-creation 🐞 (created on 2023-12-26, confidence: 85.0%)
6. 🟢 **[#17741](https://github.com/hashicorp/terraform-provider-google/issues/17741)** - google_compute_backend_service.protocol documentation outdated 🐞 (created on 2024-04-02, confidence: 85.0%)
7. 🟢 **[#19189](https://github.com/hashicorp/terraform-provider-google/issues/19189)** - google_compute_forwarding_rule should be recreated when used for PSC and target is changing 🐞 (created on 2024-08-20, confidence: 85.0%)
8. 🟢 **[#6697](https://github.com/hashicorp/terraform-provider-google/issues/6697)** - Conditional IAM resulting into duplicate roles (one with condition and one without condition created during enabeling API) 🐞 (created on 2020-06-25, confidence: 75.0%)
9. 🟢 **[#10118](https://github.com/hashicorp/terraform-provider-google/issues/10118)** - google_monitoring_alert_policy, google_monitoring_dashboard, google_logging_metric when using for each cycle always requests changes for TF apply/plan 🐞 (created on 2021-09-21, confidence: 75.0%)
10. 🟢 **[#11368](https://github.com/hashicorp/terraform-provider-google/issues/11368)** - Creation of google_logging_project_bucket_config fails when project used to run Terraform SA does not have billing enabled 🐞 (created on 2022-03-29, confidence: 75.0%)
11. 🟢 **[#13503](https://github.com/hashicorp/terraform-provider-google/issues/13503)** - failed update to google_iap_web_backend_service_iam_member 🐞 (created on 2023-01-17, confidence: 75.0%)
12. 🟢 **[#15970](https://github.com/hashicorp/terraform-provider-google/issues/15970)** - Terraform tries adding TYPE_UNSPECIFIED to header match in google_network_services_grpc_route on every run 🐞 (created on 2023-09-25, confidence: 75.0%)
13. 🟢 **[#18443](https://github.com/hashicorp/terraform-provider-google/issues/18443)** - Plan changes on every execution even though there are no changes to the code 🐞 (created on 2024-06-14, confidence: 75.0%)
14. 🟢 **[#18710](https://github.com/hashicorp/terraform-provider-google/issues/18710)** - Modify google_compute_service_attachment resource so it can support secure web proxy as a target service 🐞 (created on 2024-07-11, confidence: 75.0%)
15. 🟢 **[#21069](https://github.com/hashicorp/terraform-provider-google/issues/21069)** - google_compute_region_url_map > path_matcher > default_service : optional but required. 🐞 (created on 2025-01-28, confidence: 75.0%)
16. 🟢 **[#21837](https://github.com/hashicorp/terraform-provider-google/issues/21837)** - When expanding the plan for XXX to include new values learned so far during apply, provider "registry.terraform.io/hashicorp/google" produced an invalid new value for 🐞 (created on 2025-03-12, confidence: 75.0%)
17. 🟢 **[#22565](https://github.com/hashicorp/terraform-provider-google/issues/22565)** - When a cloud run deployment fails terraform apply fails but subsequent plans show no diff 🐞 (created on 2025-04-30, confidence: 75.0%)
18. 🟢 **[#23039](https://github.com/hashicorp/terraform-provider-google/issues/23039)** - Cannot add `network` argument to existing `google_compute_region_backend_service` resource 🐞 (created on 2025-05-26, confidence: 75.0%)
19. 🟢 **[#24239](https://github.com/hashicorp/terraform-provider-google/issues/24239)** - Multiple apply executions are required to create a Cloud SQL instance with outbound PSC 🐞 (created on 2025-09-02, confidence: 75.0%)
20. 🟢 **[#6073](https://github.com/hashicorp/terraform-provider-google/issues/6073)** - Add global load balancer IP ranges to google_netblock_ip_ranges (created on 2020-04-08, confidence: 85.0%)
21. 🟢 **[#7742](https://github.com/hashicorp/terraform-provider-google/issues/7742)** - Make strip_query in google_compute_url_map optional (created on 2020-11-09, confidence: 85.0%)
22. 🟢 **[#8607](https://github.com/hashicorp/terraform-provider-google/issues/8607)** - Add support for L4 ILB NEG (created on 2021-03-03, confidence: 85.0%)
23. 🟢 **[#9536](https://github.com/hashicorp/terraform-provider-google/issues/9536)** - google_compute_url_map: support testing headers, and URL redirects/rewrites (created on 2021-07-09, confidence: 85.0%)
24. 🟢 **[#10784](https://github.com/hashicorp/terraform-provider-google/issues/10784)** - google_compute_url_map: Large diffs on simple changes (created on 2021-12-22, confidence: 85.0%)
25. 🟢 **[#11045](https://github.com/hashicorp/terraform-provider-google/issues/11045)** - google_compute_forwarding_rule backend_service documentation incorrect (created on 2022-02-07, confidence: 85.0%)
26. 🟢 **[#11354](https://github.com/hashicorp/terraform-provider-google/issues/11354)** - Create Google managed SSL certificate for Kubernetes Ingress using Terraform (created on 2022-03-26, confidence: 85.0%)
27. 🟢 **[#12507](https://github.com/hashicorp/terraform-provider-google/issues/12507)** - Add name validation for load balancer resources. (created on 2022-09-08, confidence: 85.0%)
28. 🟢 **[#12617](https://github.com/hashicorp/terraform-provider-google/issues/12617)** - request_coalescing missing from google_compute_backend_service cdn config (created on 2022-09-21, confidence: 85.0%)
29. 🟢 **[#13429](https://github.com/hashicorp/terraform-provider-google/issues/13429)** - IAM policy for Identity-Aware Proxy WebBackendService does not support region scope backend services (created on 2023-01-10, confidence: 85.0%)
30. 🟢 **[#13940](https://github.com/hashicorp/terraform-provider-google/issues/13940)** - URL Map Host Rule and Path Matcher Resource (created on 2023-03-08, confidence: 85.0%)
31. 🟢 **[#16241](https://github.com/hashicorp/terraform-provider-google/issues/16241)** - Terraform support for all frontend ports of Application Load Balancers (created on 2023-10-13, confidence: 85.0%)
32. 🟢 **[#17457](https://github.com/hashicorp/terraform-provider-google/issues/17457)** - Ambiguous instantiation of health checks resource objects  (created on 2024-02-29, confidence: 85.0%)
33. 🟢 **[#17965](https://github.com/hashicorp/terraform-provider-google/issues/17965)** - Correct usage of "service_directory_registrations" block in "google_compute_forwarding_rule" with PSC / Private Service Connect? (created on 2024-04-26, confidence: 85.0%)
34. 🟢 **[#18060](https://github.com/hashicorp/terraform-provider-google/issues/18060)** - When configuring a cross-project backend service for a load balancer, the backend service refers host project. (created on 2024-05-09, confidence: 85.0%)
35. 🟢 **[#18894](https://github.com/hashicorp/terraform-provider-google/issues/18894)** -  routeRules do not work for External load balancers (created on 2024-07-29, confidence: 85.0%)
36. 🟢 **[#19395](https://github.com/hashicorp/terraform-provider-google/issues/19395)** - Missing customErrorResponsePolicy field in route rules in google_compute_url_map (created on 2024-09-06, confidence: 85.0%)
37. 🟢 **[#23095](https://github.com/hashicorp/terraform-provider-google/issues/23095)** - Allow setting global access in a pre-existing ILB forwarding rule by recreating resource (created on 2025-05-30, confidence: 85.0%)
38. 🟢 **[#24037](https://github.com/hashicorp/terraform-provider-google/issues/24037)** - Add data for google_compute_url_map (created on 2025-08-19, confidence: 85.0%)
39. 🟢 **[#24173](https://github.com/hashicorp/terraform-provider-google/issues/24173)** - Add new resource to support Cloud Load Balancer Edge extension (created on 2025-08-27, confidence: 85.0%)
40. 🟢 **[#9259](https://github.com/hashicorp/terraform-provider-google/issues/9259)** - Discover web_backend_service name created previously from k8s api (created on 2021-05-28, confidence: 75.0%)
41. 🟢 **[#9615](https://github.com/hashicorp/terraform-provider-google/issues/9615)** - Add plural `google_compute_ssl_certificates` data source, with ability to set a `filter` (created on 2021-07-22, confidence: 75.0%)
42. 🟢 **[#9712](https://github.com/hashicorp/terraform-provider-google/issues/9712)** - Node Pool Datasources (created on 2021-08-03, confidence: 75.0%)
43. 🟢 **[#11046](https://github.com/hashicorp/terraform-provider-google/issues/11046)** - url_map and dynamic "route_rules" ordering issue (created on 2022-02-07, confidence: 75.0%)
44. 🟢 **[#12519](https://github.com/hashicorp/terraform-provider-google/issues/12519)** - Documentation: Appropriate formatting for callouts (created on 2022-09-09, confidence: 75.0%)
45. 🟢 **[#16152](https://github.com/hashicorp/terraform-provider-google/issues/16152)** - Failing test(s): TestAccEdgecontainerNodePool_edgecontainerLocalControlPlaneNodePoolInternalExample (created on 2023-10-06, confidence: 75.0%)
46. 🟢 **[#17312](https://github.com/hashicorp/terraform-provider-google/issues/17312)** - google_certificate_manager_certificate: Self managed certificate update using patch instead of force replacement (created on 2024-02-19, confidence: 75.0%)
47. 🟢 **[#18766](https://github.com/hashicorp/terraform-provider-google/issues/18766)** - google_gkeonprem_bare_metal_admin_cluster does not support bgp_lb_config {} (created on 2024-07-17, confidence: 75.0%)
48. 🟢 **[#18941](https://github.com/hashicorp/terraform-provider-google/issues/18941)** - Compute instance groups plural datasource (created on 2024-07-31, confidence: 75.0%)
49. 🟢 **[#19437](https://github.com/hashicorp/terraform-provider-google/issues/19437)** - Add support for specifying location for google_certificate_manager_certificate_map and google_certificate_manager_certificate_map_entry (created on 2024-09-11, confidence: 75.0%)
50. 🟢 **[#19548](https://github.com/hashicorp/terraform-provider-google/issues/19548)** - Add a new `compute_global_forwarding_rules` data source (created on 2024-09-20, confidence: 75.0%)
51. 🟢 **[#20052](https://github.com/hashicorp/terraform-provider-google/issues/20052)** - Add filter argument to forwarding_rules data source (created on 2024-10-28, confidence: 75.0%)
52. 🟢 **[#23397](https://github.com/hashicorp/terraform-provider-google/issues/23397)** - Unclear documentation for how to create regional Private Service Connect endpoints (created on 2025-06-25, confidence: 75.0%)
53. 🟢 **[#23475](https://github.com/hashicorp/terraform-provider-google/issues/23475)** - Failing test(s): TestAccNetworkSecurityBackendAuthenticationConfig_backendServiceTlsSettingsExample (created on 2025-07-01, confidence: 75.0%)
54. 🟢 **[#23612](https://github.com/hashicorp/terraform-provider-google/issues/23612)** - Documentation - Add https proxies to compute_ssl_policy resource (created on 2025-07-15, confidence: 75.0%)
55. 🟢 **[#23950](https://github.com/hashicorp/terraform-provider-google/issues/23950)** - Define default value for load_balancing_scheme as EXTERNAL_MANAGED instead of EXTERNAL (created on 2025-08-11, confidence: 75.0%)

### Cloud Armor (21 issues)

1. 🟢 **[#17062](https://github.com/hashicorp/terraform-provider-google/issues/17062)** - The docs need updating for the `name` attribute of `google_recaptcha_enterprise_key` 🐞 (created on 2024-01-22, confidence: 90.0%)
2. 🟢 **[#8335](https://github.com/hashicorp/terraform-provider-google/issues/8335)** - Terraform plan with 'google_compute_security_policy' not show the creation of existing resources 🐞 (created on 2021-01-29, confidence: 85.0%)
3. 🟢 **[#14599](https://github.com/hashicorp/terraform-provider-google/issues/14599)** - Validation for unique priority fields in google_compute_security_policy 🐞 (created on 2023-05-15, confidence: 85.0%)
4. 🟢 **[#16638](https://github.com/hashicorp/terraform-provider-google/issues/16638)** - `google_compute_security_policy` cannot correct drift from the UI when `enforce_on_key` is used 🐞 (created on 2023-11-30, confidence: 85.0%)
5. 🟢 **[#17275](https://github.com/hashicorp/terraform-provider-google/issues/17275)** - Error 400: Invalid value for field `resource.rateLimitOptions` when tuning cloud armor rules? 🐞 (created on 2024-02-14, confidence: 85.0%)
6. 🟢 **[#19993](https://github.com/hashicorp/terraform-provider-google/issues/19993)** - Preconfigured WAF config not working at google_compute_region_security_policy_rule 🐞 (created on 2024-10-24, confidence: 85.0%)
7. 🟢 **[#20892](https://github.com/hashicorp/terraform-provider-google/issues/20892)** - Gateway Security Policy Rule failing when creating multiple 🐞 (created on 2025-01-13, confidence: 85.0%)
8. 🟢 **[#21186](https://github.com/hashicorp/terraform-provider-google/issues/21186)** - Error 400: Invalid value for field resource.rateLimitOptions When setting rate_limit_options.exceed_action to redirect in google_compute_security_policy 🐞 (created on 2025-01-31, confidence: 85.0%)
9. 🟢 **[#15686](https://github.com/hashicorp/terraform-provider-google/issues/15686)** - google_compute_network_edge_security_service showing diff for security_policy 🐞 (created on 2023-08-30, confidence: 75.0%)
10. 🟢 **[#20949](https://github.com/hashicorp/terraform-provider-google/issues/20949)** - Unable to update preview status on google_compute_region_security_policy_rule 🐞 (created on 2025-01-17, confidence: 75.0%)
11. 🟢 **[#14495](https://github.com/hashicorp/terraform-provider-google/issues/14495)** - reCAPTCHA does not return the Legacy reCAPTCHA secret key (created on 2023-05-04, confidence: 90.0%)
12. 🟢 **[#14555](https://github.com/hashicorp/terraform-provider-google/issues/14555)** - Doc: missing description section for google_recaptcha_enterprise_key (created on 2023-05-10, confidence: 90.0%)
13. 🟢 **[#19707](https://github.com/hashicorp/terraform-provider-google/issues/19707)** - Align google_recaptcha_enterprise_key samples with customer use cases (created on 2024-10-01, confidence: 90.0%)
14. 🟢 **[#7965](https://github.com/hashicorp/terraform-provider-google/issues/7965)** - Add support for atomically updating multiple rules in a security policy (created on 2020-12-08, confidence: 85.0%)
15. 🟢 **[#14896](https://github.com/hashicorp/terraform-provider-google/issues/14896)** - Request to Add 'dest_fqdns', 'dest_region_codes', 'dest_threat_intelligences', 'src_fqdns', 'src_region_codes', and 'src_threat_intelligences' to Organizational Security Rules (created on 2023-06-13, confidence: 85.0%)
16. 🟢 **[#17288](https://github.com/hashicorp/terraform-provider-google/issues/17288)** - Dynamic Cloud Armor Rule Ignore Conflict (created on 2024-02-15, confidence: 85.0%)
17. 🟢 **[#17993](https://github.com/hashicorp/terraform-provider-google/issues/17993)** - add labels to google_compute_region_security_policy and google_compute_security_policy (created on 2024-05-01, confidence: 85.0%)
18. 🟢 **[#9874](https://github.com/hashicorp/terraform-provider-google/issues/9874)** - 409s when SIGTERM/cancel/CTRL+C terraform while creating a resource which involves an Operation (created on 2021-08-20, confidence: 75.0%)
19. 🟢 **[#17095](https://github.com/hashicorp/terraform-provider-google/issues/17095)** - Support Firebase App Check (created on 2024-01-24, confidence: 75.0%)
20. 🟢 **[#18624](https://github.com/hashicorp/terraform-provider-google/issues/18624)** - Add purpose field to google_network_security_address_group. (created on 2024-07-02, confidence: 75.0%)
21. 🟢 **[#23488](https://github.com/hashicorp/terraform-provider-google/issues/23488)** - Cannot target a project with google_compute_organization_security_policy_association (created on 2025-07-02, confidence: 75.0%)


## Next Steps

1. Select the most suitable issues for contribution
2. Prioritize bugs, as they have greater impact for users
3. Consider issues with higher classification confidence and more recent ones


## Note on Classification Reliability

The classification of issues by service was performed using a hybrid approach that combines:
- Preliminary verification of critical keywords
- Semantic analysis with TF-IDF (70% of the score)
- Specific pattern matching (30% of the score)

The confidence in the classification is indicated for each issue using the following icons:
- 🟢 High confidence (70-100%)
- 🟡 Medium confidence (50-70%)
- 🟠 Low confidence (30-50%)
