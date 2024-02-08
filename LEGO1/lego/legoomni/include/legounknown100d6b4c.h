#ifndef LEGOUNKNOWN100D6B4C_H
#define LEGOUNKNOWN100D6B4C_H

#include "decomp.h"
#include "legocachesound.h"
#include "mxstl/stlcompat.h"
#include "mxtypes.h"

struct Element1006b4c {
	Element1006b4c() : m_sound(NULL), m_name(NULL){};
	Element1006b4c(LegoCacheSound* p_sound, const char* p_name) : m_sound(p_sound), m_name(p_name){};
	Element1006b4c(LegoCacheSound* p_sound) : m_sound(p_sound), m_name(p_sound->GetString0x48().GetData()){};
	~Element1006b4c()
	{
		if (m_sound == NULL && m_name != NULL) {
			delete[] const_cast<char*>(m_name);
		}
	}
	bool operator==(Element1006b4c) const { return 0; }
	bool operator<(Element1006b4c) const { return 0; }

	LegoCacheSound* m_sound;
	const char* m_name;
};

struct Map100d6b4cComparator {
	bool operator()(const Element1006b4c& p_a, const Element1006b4c& p_b) const
	{
		return strcmpi(p_a.m_name, p_b.m_name) > 0;
	}
};

typedef set<Element1006b4c, Map100d6b4cComparator> Map100d6b4c;

typedef list<Element1006b4c> List100d6b4c;

// VTABLE: LEGO1 0x100d6b4c
// SIZE 0x20
class LegoUnknown100d6b4c {
public:
	LegoUnknown100d6b4c(){};
	~LegoUnknown100d6b4c();

	virtual MxResult Tickle(); // vtable+0x00

	void FUN_1003d170(const char* p_key);
	LegoCacheSound* FUN_1003d290(LegoCacheSound* p_sound);
	void FUN_1003dc40(LegoCacheSound** p_und);

private:
	Map100d6b4c m_map;
	List100d6b4c m_list;
};

// TODO: Function names subject to change.

// clang-format off

// TEMPLATE: LEGO1 0x10029c30
// _Tree<Element1006b4c,Element1006b4c,set<Element1006b4c,Map100d6b4cComparator,allocator<Element1006b4c> >::_Kfn,Map100d6b4cComparator,allocator<Element1006b4c> >::~_Tree<Element1006b4c,Element1006b4c,set<Element1006b4c,Map100d6b4cComparator,allocator<Element1006b4c> >::_Kfn,Map100d6b4cComparator,allocator<Element1006b4c> >

// TEMPLATE: LEGO1 0x10029d10
// _Tree<Element1006b4c,Element1006b4c,set<Element1006b4c,Map100d6b4cComparator,allocator<Element1006b4c> >::_Kfn,Map100d6b4cComparator,allocator<Element1006b4c> >::iterator::_Inc

// TEMPLATE: LEGO1 0x10029d50
// _Tree<Element1006b4c,Element1006b4c,set<Element1006b4c,Map100d6b4cComparator,allocator<Element1006b4c> >::_Kfn,Map100d6b4cComparator,allocator<Element1006b4c> >::erase

// TEMPLATE: LEGO1 0x1002a1b0
// _Tree<Element1006b4c,Element1006b4c,set<Element1006b4c,Map100d6b4cComparator,allocator<Element1006b4c> >::_Kfn,Map100d6b4cComparator,allocator<Element1006b4c> >::_Erase

// TEMPLATE: LEGO1 0x1002a210
// list<Element1006b4c,allocator<Element1006b4c> >::~list<Element1006b4c,allocator<Element1006b4c> >

// TEMPLATE: LEGO1 0x1002a2a0
// map<char const *,LegoCacheSound *,Map100d6b4cComparator,allocator<LegoCacheSound *> >::~map<char const *,LegoCacheSound *,Map100d6b4cComparator,allocator<LegoCacheSound *> >

// TEMPLATE: LEGO1 0x1002a2f0
// Map<char const *,LegoCacheSound *,Map100d6b4cComparator>::~Map<char const *,LegoCacheSound *,Map100d6b4cComparator>

// TEMPLATE: LEGO1 0x1002a340
// List<Element1006b4c>::~List<Element1006b4c>

// TEMPLATE: LEGO1 0x1003d450
// LegoUnknown100d6b4c::Tree::insert

// TEMPLATE: LEGO1 0x1003d6f0
// LegoUnknown100d6b4c::Tree::_Dec

// TEMPLATE: LEGO1 0x1003d740
// LegoUnknown100d6b4c::Tree::_BuyNode

// TEMPLATE: LEGO1 0x1003d760
// LegoUnknown100d6b4c::Tree::_Insert

// GLOBAL: LEGO1 0x100f31cc
// _Tree<Element1006b4c,Element1006b4c,set<Element1006b4c,Map100d6b4cComparator,allocator<Element1006b4c> >::_Kfn,Map100d6b4cComparator,allocator<Element1006b4c> >::_Nil

// clang-format on

#endif // LEGOUNKNOWN100D6B4C_H
