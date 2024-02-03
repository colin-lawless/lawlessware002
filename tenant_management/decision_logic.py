# tenant_management.decision_logic.py
# Ayush

# Updated statuses
STATUSES = [
    'active', 'should be warned', 'warned', 'should be cancelled', 
    'cancelled', 'should be sued', 'lawsuit', 'should be evicted', 'evicted'
]

def advance_status(current_status):
    try:
        # Find the index of the current status and advance it by one
        next_index = STATUSES.index(current_status) + 1
        # Ensure the index is within the range of the list
        next_index = min(next_index, len(STATUSES) - 1)
        return STATUSES[next_index]
    except ValueError:
        # Return the default status if the current status is not in the list
        return 'active'

def decide_next_action(tenant, config):
    thresholds = config['decision_thresholds']
    actions = config['action_steps']

    # Start from the most severe to the least severe status
    if tenant.days_overdue >= thresholds['should_be_evicted_threshold']:
        recommended_status = 'should be evicted'
    elif tenant.days_overdue >= thresholds['should_be_sued_threshold']:
        recommended_status = 'should be sued'
    elif tenant.days_overdue >= thresholds['should_be_cancelled_threshold']:
        recommended_status = 'should be cancelled'
    elif tenant.days_overdue >= thresholds['should_be_warned_threshold']:
        recommended_status = 'should be warned'
    else:
        recommended_status = 'na'

    # If the tenant's current status is the same as the recommended, no action is necessary
    if tenant.status == recommended_status:
        return 'na', {}, recommended_status

    # Define action and action_steps based on the recommended status
    action = recommended_status
    action_steps = actions.get(recommended_status, {})

    return action, action_steps, recommended_status
