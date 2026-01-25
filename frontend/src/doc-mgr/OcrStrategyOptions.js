export const ocrStrategyLabels = {
  use_document_set: 'Use Document Set',
  hi_res: 'Hi-Res',
  fast: 'Fast',
  ocr_only: 'OCR Only'
}

export const ocrStrategyOptions = [
  { value: 'use_document_set', title: ocrStrategyLabels.use_document_set },
  { value: 'hi_res', title: ocrStrategyLabels.hi_res },
  { value: 'fast', title: ocrStrategyLabels.fast },
  { value: 'ocr_only', title: ocrStrategyLabels.ocr_only }
]

export const ocrStrategyOptionsForDocSet = ocrStrategyOptions.filter(
  (option) => option.value !== 'use_document_set'
)
