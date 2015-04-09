/*****************************************************************************
 *   MindTheGap: Integrated detection and assembly of insertion variants
 *   A tool from the GATB (Genome Assembly Tool Box)
 *   Copyright (C) 2014  INRIA
 *   Authors: C.Lemaitre, G.Rizk
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Affero General Public License as
 *  published by the Free Software Foundation, either version 3 of the
 *  License, or (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Affero General Public License for more details.
 *
 *  You should have received a copy of the GNU Affero General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *****************************************************************************/

#ifndef _TOOL_FindBreakpoints_HPP_
#define _TOOL_FindBreakpoints_HPP_

/********************************************************************************/
#include <memory>
#include <gatb/gatb_core.hpp>
#include <Finder.hpp>
//#include <IFindObserver.hpp>

/********************************************************************************/

template<size_t type>
class IFindObserver;

template<size_t span>
class FindBreakpoints
{
public :

    // Constructor
    FindBreakpoints(Finder * find);

    //Functor
    void operator()();

    // Observable
    void notify();
    void addObserver(IFindObserver<span>* new_obs);

public :

    typedef typename gatb::core::kmer::impl::Kmer<span>::ModelCanonical KmerModel;
    typedef typename KmerModel::Iterator KmerIterator;
    typedef typename gatb::core::kmer::impl::Kmer<span>::Type KmerType;

public :

    /*Write breakpoint*/
    uint64_t breakpoint_id;
    uint64_t position;
    char * chrom_sequence;
    string chrom_name;

    /*Kmer related object*/
    KmerModel model;
    KmerType kmer_begin;
    KmerType kmer_end;
    KmerType previous_kmer;

    /*Gap type detection*/
    uint64_t solid_stretch_size;
    uint64_t gap_stretch_size;
    uint64_t previous_gap_stretch_size;

    Finder * finder;

private :

    std::vector<std::unique_ptr<IFindObserver<span> > > list_obs;
};

template<size_t span>
FindBreakpoints<span>::FindBreakpoints(Finder * find) : list_obs()
{
    this->breakpoint_id = 0;
    this->position = 0;
    this->chrom_sequence = NULL;
    this->chrom_name = "";

    this->solid_stretch_size = 0;
    this->gap_stretch_size = 0;
    this->previous_gap_stretch_size = 0;

    this->finder = find;
}

template<size_t span>
void FindBreakpoints<span>::operator()()
{
    BankFasta::Iterator it_seq(*(finder->_refBank));
    KmerIterator it_kmer (model);

    for (it_seq.first(); !it_seq.isDone(); it_seq.next())
    {
	solid_stretch_size = 0;
	gap_stretch_size = 0;
	previous_gap_stretch_size = 0;
		
	// We set the data from which we want to extract kmers.
	it_kmer.setData (it_seq->getData());
	char* chrom_sequence = it_seq->getDataBuffer();
	string chrom_name = it_seq->getComment();
	uint64_t position=0;
	
	// We iterate the kmers.
	for (it_kmer.first(); !it_kmer.isDone(); it_kmer.next(), position++)
	{
	    //we need to convert the kmer in a node to query the graph.
	    Node node(Node::Value(it_kmer->value()));

	    if (this->finder->_graph.contains(node)) //the kmer is indexed
	    {
		solid_stretch_size++;

		this->notify();

		if (solid_stretch_size > 1) gap_stretch_size = 0; // du coup on sort le trou a tai indexed ==2, gap_stretch_size pas remis a 0 par solide isole (FP)
		if (solid_stretch_size==1) kmer_end = it_kmer->forward(); // kmer_end should be first kmer indexed after a hole
		if(gap_stretch_size) previous_gap_stretch_size = gap_stretch_size;
	    }
	    else //kmer is not indexed, measure size of the zone not covered by kmers of the reads
	    {
		if(solid_stretch_size==1)
		{
		    gap_stretch_size = previous_gap_stretch_size + solid_stretch_size ; //inutile maintenant il me semble, car tai_not_indexed non reset par FP
		}
		if(solid_stretch_size > 1) // begin of not indexed zone
		{
		    kmer_begin = previous_kmer ;
		}
		gap_stretch_size ++;
		solid_stretch_size =0;
	    }
	    previous_kmer = it_kmer->forward();

	}
    }
}

template<size_t span>
void FindBreakpoints<span>::notify()
{
    for(auto it = this->list_obs.begin(); it != this->list_obs.end(); it++)
    {
	(*it)->update();
    }
}

template<size_t span>
void FindBreakpoints<span>::addObserver(IFindObserver<span>* new_obs)
{
    this->list_obs.push_back(std::unique_ptr<IFindObserver<span> >(new_obs));
}

#endif /* _TOOL_FindBreakpoints_HPP_ */
