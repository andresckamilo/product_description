import writer as wf
from prompts import base_prompts, seo_keywords, user_prompt, seo_keywords_sp, user_sp

def _generate_product_description(product_info:dict, **kwargs):
   
   prompt = kwargs['prompt'].format(**product_info)
   system = kwargs['system']
   description = _run_model(system=system, prompt=prompt)
   return description.choices[0].message.content


def _run_model(model:str = 'gpt-4o',*, system:str,prompt:str):
    import os
    from dotenv import load_dotenv
    from openai import OpenAI
    import instructor
    import logfire

    load_dotenv()

    logfire.configure(token=os.getenv("LOGFIRE_API_KEY"))

    client = instructor.patch(
        OpenAI(
        )
    )
    logfire.instrument_openai(client)

    return client.chat.completions.create(
        messages = [
        {
            "role": "system",
            "content": system,
        },
        {"role": "user", "content": f""" {prompt}
        """},
    ], 
        model=model,
    )

def _run_model_plotly(model:str = 'gpt-4o',*, system:str,prompt:str):
    import os
    from dotenv import load_dotenv
    from openai import OpenAI
    import instructor
    import logfire
    from pydantic import BaseModel, Field

    class Plotly(BaseModel):
        output_plotly: str = Field(..., description = 'The plotly in JSON Format')
        keyword_analysis: str = Field(..., description = 'Values of the keyword analysis')

    load_dotenv()

    logfire.configure(token=os.getenv("LOGFIRE_API_KEY"))

    client = instructor.patch(
        OpenAI(
        )
    )
    logfire.instrument_openai(client)

    return client.chat.completions.create(
        messages = [
        {
            "role": "system",
            "content": system,
        },
        {"role": "user", "content": f""" {prompt}
        """},
    ], 
        model=model,
        response_model=Plotly,
    )


def handle_click(state):
   state["product_descriptions"]["visible"] = False

   # Loop through all the base prompts to generate versions tailored to each outlet
   for outlet, base_prompt in base_prompts.items():
       state["message"] = f"% Generating product description for {outlet}..."
       product_description = _generate_product_description(product_info=state["form"].to_dict(),**base_prompt)
       state["product_descriptions"]["outlets"][outlet] = product_description


    # Create the SEO analysis
   state["message"] = "Analyzing SEO keywords..."
   outlets = state["product_descriptions"]["outlets"]
   state["seo_analysis"]["outlets"] = _generate_seo_keywords(outlets)
   state["seo_analysis"]["visible"] = True

   print(state["seo_analysis"])
   state["product_descriptions"]["visible"] = True
   state["message"] = ""

def _generate_seo_keywords(outlets):
   combined_descriptions = "\n".join(f"{key}: {value}" for key, value in outlets.items())

   # Generate the prompt with the provided descriptions
   prompt = seo_keywords.format(descriptions=combined_descriptions)
   # Strip out whitespace and backticks from the response
   return _run_model_plotly(system = seo_keywords_sp,prompt=prompt).model_dump()['output_plotly']


wf.init_state({
   "form": {
       "title": "",
       "description": "",
       "keywords": ""
   },
   "message": "Fill in the inputs and click \"Generate\" to get started.",
   "product_descriptions": {
       "visible": False,
       "outlets": {}
   },
   "seo_analysis": {
       "visible": False,
       "outlets": {}
   }
})


