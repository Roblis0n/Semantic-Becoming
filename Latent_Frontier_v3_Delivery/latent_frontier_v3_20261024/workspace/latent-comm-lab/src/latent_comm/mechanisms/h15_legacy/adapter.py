from latent_comm.core import ContractError

def population_forward(sender_state,sender_writer,receiver_readers,receiver_functions,receiver_inputs,*,capability_projection=None,capability_vector=None):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if sender_state.ndim!=2 or sender_writer.ndim!=2 or sender_writer.shape[1]!=sender_state.shape[-1]:raise ContractError('DimensionMismatch','sender projection [protocol,source]')
    message=sender_state@sender_writer.T
    if capability_projection is not None:
        if capability_vector is None or capability_vector.shape[0]!=message.shape[0] or capability_projection.shape!=(message.shape[-1],capability_vector.shape[-1]):raise ContractError('DimensionMismatch','public capability vector, never model identity or answer labels')
        message=message+capability_vector@capability_projection.T
    outputs=[]
    if not len(receiver_readers)==len(receiver_functions)==len(receiver_inputs):raise ContractError('DimensionMismatch','one dedicated reader per receiver')
    for reader,receiver,inputs in zip(receiver_readers,receiver_functions,receiver_inputs):
        if reader.shape[1]!=message.shape[-1]:raise ContractError('DimensionMismatch','receiver protocol width')
        state=message@reader.T;outputs.append(receiver(state,inputs))
    return message,tuple(outputs) # Frozen receiver weights retain input-to-output autograd.
