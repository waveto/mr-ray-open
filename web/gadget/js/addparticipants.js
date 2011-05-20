/*
Copyright 2011 Acknack Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
/*
* INTERFACE that you robot can use
*
* EMAIL-PARTICIPANTS : contains JSON list of all email participants
* ADD-PARTICIPANT : the participant to be added. If this is not null this user needs to be added to the wave. Null the value after the user has been added and set add the participant to the EMAIL-PARTICIPANTS list
*/
(function($) {
    var participantBeingAdded = null;
	
	/**
	* Functions that can be used to generate elements
	*/
	var elementFactory = {
		workingImage	: 	function() {
			var image = $(document.createElement("img"));
			image.attr("id", "add_participant_working");
	        image.attr("src", "http://mr-ray.appspot.com/web/media/working.gif");
	        return image;
		},
		addButton		: 	function(methodToBind) {
			var button = $(document.createElement("input"));
	        button.attr("type", "button");
	        button.attr("id", "add_participant_butt");
			button.attr("value", "Add");
	        button.attr("class", "ui-state-default ui-corner-all");
	        button.click(methodToBind);
	        button.hover(function() {
	            $(this).addClass('ui-state-hover');
	        }, function() {
	            $(this).removeClass('ui-state-hover');
	        });
	        return button;
		},
		participantField: 	function() {
			var input = $(document.createElement("input"));
			input.attr("type", "text");
			input.attr("id", "add_participant_input");
			input.attr("name", "add_participant_input");
			return input;
		},
		listItem		: 	function(text) {
			return $(document.createElement("li")).text(text);
		},
        errorItem       :   function(text) {
			var errorContainer = $(document.createElement("div"));
			errorContainer.attr("id", "errors");
            var error = $(document.createElement("p"));
            error.text(text);
			errorContainer.append(error);
            return errorContainer;
        }
	};
	
	/**
	* Converts the add button to a working image
	*/
	function buttonToImage() {
		var button = $("#add_participant_butt");
		var image = elementFactory.workingImage();
		var parent = button.parent();
		
		button.remove();
		parent.append(image);
	}
	
	/**
	* Converts the working image to an add button
	*/
	function imageToButton() {
		var image = $("#add_participant_working");
		var button = elementFactory.addButton(eventFactory.addParticipant);
		var parent = image.parent();
		
		image.remove();
		parent.append(button);
	}
    
    /**
    * Checks that an email looks valid
    */
    function isEmailValid(email) {
        var emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/;
        return emailPattern.test(email);
    }
    
    /**
    * Deletes an elements children
    */
    function deleteChildren(element) {
        element.children().remove();
    }
    
    /**
    * Produces error for the user
    */
    function insertError(errorMessage) {
		$('#errors').remove();
        $('#gadget_content').append(elementFactory.errorItem(errorMessage));
    }
    
    /**
    * Returns an array of participants sorted by name
    */
    function getEmailParticipants(state) {
        var participantsJSON = state.get("EMAIL-PARTICIPANTS");
        if(participantsJSON === null) {
            return [];
        } else {
            participantsJSON = Base64.decode(participantsJSON);
            return JSON.parse(participantsJSON).sort();
        }
    }
    
    /**
    * Checks if the new participant is already in the participants list
    */
    function isParticipantAlreadyPresent(participant, state) {
    	var participants = getEmailParticipants(wave.getState());
    	for(var i = 0; i < participants.length; i++) {
    		if(participant === participants[i]) {
    			return true;
    		}	
    	}
    	return false;
    }
	
	/**
	* Functions that can be bound to events
	*/
	var eventFactory = {
		addParticipant	: 	function() {
			//Extract the value and submit to wave
	        var newParticipantElem = $("#add_participant_input")
	        var participantToAdd = newParticipantElem.val();
	        var state = wave.getState();
			if(isEmailValid(participantToAdd)) {
				if(!isParticipantAlreadyPresent(participantToAdd, state)) {
					state.submitValue("ADD-PARTICIPANT", participantToAdd);
		        	participantBeingAdded = participantToAdd;
	
		        	//Change the GUI to inform user
		        	newParticipantElem.val("");
		        	buttonToImage();
					$('#errors').remove();
				} else {
					insertError("The user has already been added");
				}
			} else {
                if(participantToAdd === "") {
                    insertError("The e-mail address cannot be blank");
                } else {
                    insertError("'" + participantToAdd + "' is not a valid e-mail address.");
                }
            }
            gadgets.window.adjustHeight();
            return false;
		}
	}

	/**
    * Returns true if the state and in mem variable dictates that the user has been added
    */
    function hasUserBeenAdded(state) {
        if(participantBeingAdded !== null) {
            var participants = getEmailParticipants(state);
            for(i in participants) {
                if(participants[i] === participantBeingAdded) {
                    return true;
                }
            }
        }
        return false;
    }
    
    /**
    * Redraws the gadget
    */
    function update() {
        var state = wave.getState();
        
        //Update the list of participants
        var participantsList = $("#participants_list");
        deleteChildren(participantsList);
        var participants = getEmailParticipants(state);
        for(var i in participants) {
            participantsList.append(elementFactory.listItem(participants[i]));
        }
        
        //Update the button
        if(hasUserBeenAdded(state)) {
            participantBeingAdded = null;
            imageToButton();
        }
        gadgets.window.adjustHeight();
    }
    
	/**
	* Google API initializing--registering handler etc
	*/
	function init() {
		if (wave && wave.isInWaveContainer()) {
			wave.setStateCallback(update);
		}
	}
	gadgets.util.registerOnLoadHandler(init);
    
    /**
    * Run when document is initialized
    */
    $(document).ready(function() {
        var addParticipantForm = $("#add_participant_form");
		var table = $(document.createElement("table"));
		var row = $(document.createElement("tr"));
		var cell1 = $(document.createElement("td")).attr("class", "add_participant_input_container");
		var cell2 = $(document.createElement("td"));
		
		addParticipantForm.append(table.append(row));
		row.append(cell1.append(elementFactory.participantField()));
		row.append(cell2.append(elementFactory.addButton(eventFactory.addParticipant)));
        
        addParticipantForm.bind('submit', eventFactory.addParticipant);
        gadgets.window.adjustHeight();
    });
	
})(jQuery);