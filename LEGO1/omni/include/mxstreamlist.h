#ifndef MXSTREAMLIST_H
#define MXSTREAMLIST_H

#include "mxdsstreamingaction.h"
#include "mxdssubscriber.h"
#include "mxnextactiondatastart.h"
#include "mxstl/stlcompat.h"

template <class T>
class MxStreamList : public list<T> {
public:
	MxBool PopFront(T& p_obj)
	{
		if (this->empty()) {
			return FALSE;
		}

		p_obj = this->front();
		this->pop_front();
		return TRUE;
	}
};

// SIZE 0x0c
class MxStreamListMxDSAction : public MxStreamList<MxDSAction*> {
public:
	MxDSAction* Find(MxDSAction* p_action, MxBool p_delete);

	// There chance this list actually holds MxDSStreamingListAction
	// instead of MxDSAction. Until then, we use this helper.
	MxBool PopFrontStreamingAction(MxDSStreamingAction*& p_obj)
	{
		if (empty()) {
			return FALSE;
		}

		p_obj = (MxDSStreamingAction*) front();
		pop_front();
		return TRUE;
	}
};

// SIZE 0x0c
class MxStreamListMxNextActionDataStart : public MxStreamList<MxNextActionDataStart*> {
public:
	MxNextActionDataStart* Find(MxU32 p_id, MxS16 p_value);
	MxNextActionDataStart* FindAndErase(MxU32 p_id, MxS16 p_value);
};

// SIZE 0x0c
class MxStreamListMxDSSubscriber : public MxStreamList<MxDSSubscriber*> {
public:
	MxDSSubscriber* Find(MxDSObject* p_object);
};

// SYNTHETIC: BETA10 0x1014f7c0
// MxStreamListMxDSSubscriber::MxStreamListMxDSSubscriber

// SYNTHETIC: BETA10 0x1014f830
// MxStreamListMxDSSubscriber::~MxStreamListMxDSSubscriber

// SYNTHETIC: BETA10 0x1014f890
// MxStreamListMxDSAction::MxStreamListMxDSAction

// SYNTHETIC: BETA10 0x1014f900
// MxStreamListMxDSAction::~MxStreamListMxDSAction

// TEMPLATE: BETA10 0x1014fa30
// MxStreamList<MxDSSubscriber *>::MxStreamList<MxDSSubscriber *>

// TEMPLATE: BETA10 0x1014faa0
// List<MxDSSubscriber *>::List<MxDSSubscriber *>

// TEMPLATE: BETA10 0x1014fe90
// MxStreamList<MxDSSubscriber *>::~MxStreamList<MxDSSubscriber *>

// TEMPLATE: BETA10 0x1014fef0
// MxStreamList<MxDSAction *>::MxStreamList<MxDSAction *>

// TEMPLATE: BETA10 0x101487b0
// list<MxDSAction *,allocator<MxDSAction *> >::iterator::operator*

// TEMPLATE: BETA10 0x10148890
// list<MxDSAction *,allocator<MxDSAction *> >::begin

// TEMPLATE: BETA10 0x10148900
// list<MxDSAction *,allocator<MxDSAction *> >::end

// TEMPLATE: BETA10 0x10148930
// list<MxDSAction *,allocator<MxDSAction *> >::erase

// TEMPLATE: BETA10 0x10148a60
// list<MxDSAction *,allocator<MxDSAction *> >::_Freenode

// TEMPLATE: BETA10 0x1014fb10
// list<MxDSSubscriber *,allocator<MxDSSubscriber *> >::list<MxDSSubscriber *,allocator<MxDSSubscriber *> >

// TEMPLATE: BETA10 0x1014fb60
// list<MxDSSubscriber *,allocator<MxDSSubscriber *> >::~list<MxDSSubscriber *,allocator<MxDSSubscriber *> >

// TEMPLATE: BETA10 0x1014fd60
// list<MxDSSubscriber *,allocator<MxDSSubscriber *> >::_Buynode

// TEMPLATE: BETA10 0x1014ff60
// List<MxDSAction *>::List<MxDSAction *>

// TEMPLATE: BETA10 0x1014ffd0
// list<MxDSAction *,allocator<MxDSAction *> >::list<MxDSAction *,allocator<MxDSAction *> >

// TEMPLATE: BETA10 0x10150020
// list<MxDSAction *,allocator<MxDSAction *> >::~list<MxDSAction *,allocator<MxDSAction *> >

// TEMPLATE: BETA10 0x10150090
// list<MxDSAction *,allocator<MxDSAction *> >::erase

// TEMPLATE: BETA10 0x101500f0
// list<MxDSAction *,allocator<MxDSAction *> >::_Buynode

// TEMPLATE: BETA10 0x101501c0
// MxStreamList<MxDSAction *>::~MxStreamList<MxDSAction *>

// TEMPLATE: BETA10 0x10150830
// List<MxDSSubscriber *>::~List<MxDSSubscriber *>

// TEMPLATE: BETA10 0x10150890
// List<MxDSAction *>::~List<MxDSAction *>

// TEMPLATE: BETA10 0x10150950
// MxStreamList<MxDSAction *>::PopFront

// TEMPLATE: BETA10 0x101509a0
// list<MxDSAction *,allocator<MxDSAction *> >::empty

// TEMPLATE: BETA10 0x101509e0
// list<MxDSAction *,allocator<MxDSAction *> >::size

// TEMPLATE: BETA10 0x10150a00
// list<MxDSAction *,allocator<MxDSAction *> >::front

// TEMPLATE: BETA10 0x10150a30
// list<MxDSAction *,allocator<MxDSAction *> >::pop_front

// TEMPLATE: BETA10 0x10150a70
// MxStreamList<MxDSSubscriber *>::PopFront

// TEMPLATE: BETA10 0x10150ac0
// list<MxDSSubscriber *,allocator<MxDSSubscriber *> >::empty

// TEMPLATE: BETA10 0x10150b00
// list<MxDSSubscriber *,allocator<MxDSSubscriber *> >::size

// TEMPLATE: BETA10 0x10151020
// list<MxDSAction *,allocator<MxDSAction *> >::push_back

#endif // MXSTREAMLIST_H
