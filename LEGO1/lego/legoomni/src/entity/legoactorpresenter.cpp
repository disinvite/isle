#include "legoactorpresenter.h"

#include "legoentity.h"
#include "misc.h"

DECOMP_SIZE_ASSERT(LegoActorPresenter, 0x50)

// FUNCTION: LEGO1 0x10076c30
// FUNCTION: BETA10 0x1003d980
void LegoActorPresenter::ReadyTickle()
{
	if (CurrentWorld()) {
		m_entity = (LegoEntity*) CreateEntity("LegoActor");
		if (m_entity) {
			SetEntityLocation(m_action->GetLocation(), m_action->GetDirection(), m_action->GetUp());
			m_entity->Create(*m_action);
		}
		ProgressTickleState(e_starting);
	}
}

// FUNCTION: LEGO1 0x10076c90
void LegoActorPresenter::StartingTickle()
{
	if (m_entity->GetROI()) {
		ProgressTickleState(e_streaming);
		ParseExtra();
	}
}

// FUNCTION: LEGO1 0x10076cc0
void LegoActorPresenter::ParseExtra()
{
	MxU16 extraLength;
	char* extraData;
	m_action->GetExtra(extraLength, extraData);

	if (extraLength & USHRT_MAX) {
		char extraCopy[512];
		memcpy(extraCopy, extraData, extraLength & USHRT_MAX);
		extraCopy[extraLength & USHRT_MAX] = '\0';

		m_entity->ParseAction(extraCopy);
	}
}
