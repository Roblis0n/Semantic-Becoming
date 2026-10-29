"""Separated role views, structural splits and locked dataset construction."""
from .records import WorldRecord,SupervisionView,SplitProvenance,ProjectionContract
from .splits import StructureSignature,TemplateAssignment,SplitManifest,partition_templates,derived_provenance
from .collate import RoleBatch,EncodedRoleBatch,SupervisionBatch,PaddedField,collate_finite_numeric,collate_tensor
from .factory import WorldFactory,FactoryCursor,generate_dataset,save_cursor,load_cursor
