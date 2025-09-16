QueryGoal
'''
{
  "QueryGoal": {
    "goalId": "goal-job-eta-0001",
    "goalType": "predict_job_completion_time",
    "parameters": [
      { "key": "jobId",   "value": "JOB-7f2e3a8b-1d" },
      { "key": "dueDate", "value": @현재시간 },
     ],
    "outputSpec": [
      { "name": "completion_time", "datatype": "datetime" },
      { "name": "tardiness_s",     "datatype": "number" },
      { "name": "sla_met",         "datatype": "boolean" }
    ],
    "termination": [
      { "key": "condition", "value": "on_job_completed" },
      { "key": "timeout",   "value": "PT4H" }
    ],
    "selectedModelRef": "aas://ModelCatalog/JobETAModel@1.4.2",
    "selectedModel": {
      "modelId": "JobETAModel",
      "MetaData": "JobEtaMetaData.json",
      "outputs": ["completion_time","tardiness_s","sla_met"],
      "preconditions": { "units.time": "s", "runtime.freshness": "PT30S" },
      "container": { "image": "registry/factory/job-eta:v1.4.2", "digest": "sha256:..." },
      "catalogVersion": "1.4.2",
      "frozenAt": @현재시간
    },
    "selectionProvenance": {
      "ruleName": "SWRL:Goal2JobETA",
      "ruleVersion": "v1.0",
      "engine": "SWRL",
      "evidence": { "matched": ["goalType==predict_job_completion_time","purpose==DeliveryPrediction"] },
      "inputsHash": "sha256:...",
      "timestamp": "2025-09-12T00:00:00Z",
      "notes": ""
    },
  }
}

'''

MetaData.json
'''
{
  "modelId": "JobETAModel",
  "requiredInputs": ["JobRoute","MachineState","Calendar","SetupMatrix","WIP","Backlog"],
  "preconditions": { "units.time": "s", "runtime.freshness": "PT30S" },
  "outputs": ["completion_time","tardiness_s","sla_met"]
}

'''

bindings.yaml
'''
schema: 1
sources:
  JobRoute:
    uri: "aas://FactoryTwin/JobRoute/{jobId}"
  MachineState:
    uri: "aas://FactoryTwin/State/Machine?at={bindAt}"
    defaults: { bindAt: "@현재시간" }
  Calendar:
    uri: "file://config/factory_calendar.yaml"
  SetupMatrix:
    uri: "file://config/setup_matrix.yaml"
  WIP:
    uri: "file://state/wip/*.json"
    glob:
      sort: ["mtime:desc","name:asc"]  # 결정적 정렬
      window: { count: 5 }             # 최신 5개만
    combine:
      op: "overlay"                    # 충돌은 last-wins
      key: "partId"
  Backlog:
    uri: "file://state/backlog/*.json"
    glob:
      sort: ["mtime:desc","name:asc"]
      window: { since: "2025-09-01T00:00:00+09:00", until: "@현재시간" }
    combine:
      op: "concat"

'''