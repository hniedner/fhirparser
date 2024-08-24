# fhir_constants.py

NS = {"fhir": "http://hl7.org/fhir"}

# XPath strings as constants
FHIR_ID = './/fhir:id'
FHIR_SUBJECT_REFERENCE = './/fhir:subject/fhir:reference'
FHIR_SUBJECT_DISPLAY = './/fhir:subject/fhir:display'
FHIR_RESULT = './/fhir:result'
FHIR_OBSERVATION = './/fhir:Observation'
FHIR_CONDITION = './/fhir:Condition'
FHIR_CODE_TEXT = './/fhir:code/fhir:text'
FHIR_EFFECTIVE_DATETIME = './/fhir:effectiveDateTime'
FHIR_VALUE_QUANTITY = './/fhir:valueQuantity/fhir:value'
FHIR_RECORDED_DATE = './/fhir:recordedDate'
FHIR_CLINICAL_STATUS = './/fhir:clinicalStatus/fhir:text'
