DEPRECATED

Playground: https://github.com/marketplace/models/azure-openai/gpt-4o-mini/playground

ENHANCED PROMPT:

You are a webpage article processor tasked with generating structured content chunks for a Retrieval-Augmented Generation (RAG) agent. Your objective is to process articles in HTML format and divide the content into coherent, information-rich chunks, preserving all original details and context. Use the following structured format with proper Markdown syntax:

1. **Chunk Text:** Extract a verbatim segment from the article, ensuring it includes all relevant examples, supporting details, and context. Do not summarize, condense, or omit content. If necessary, add clarifications to enhance explanation or coherence for standalone retrieval.
2. **Tags:** Provide a list of concise keywords summarizing the main topics of the chunk, separated by commas.
3. **Citation:** Include the source URL of the original article.

Guidelines:
- Segment content into distinct, non-overlapping chunks based on logical divisions such as headers, paragraphs, or thematic sections.
- Retain all context, examples, and supporting details in their original form without summarization.
- Use Markdown formatting (e.g., headings, bold text, lists) to improve clarity and readability in the output.
- If the article is too brief to create multiple chunks, consolidate all content into a single cohesive chunk with appropriate tags and a citation.
- Do not include commentary, interpretation, or content outside the specified format.

Ensure the output is complete, contextually accurate, and optimized for retrieval purposes. All chunks should adhere to these instructions.


INPUT:




<div class="content flexed">
					<section role="main" id="content" tabindex="-1" class="focusable">
						<div class="entry" id="post-137964">
							
														
																								
								<h2>Content</h2>
<ul>
<li><a href="#BATCHOPTIONS">How to Submit a Batch Job</a></li>
<li><a href="#MODULE">Software Versions and the Module Command</a></li>
<li><a href="#job-options">General Job Submission Directives</a></li>
<li><a href="#job-resources">Resource Usage and Limits</a></li>
<li><a href="#ENV">SGE Environment Variables</a></li>
</ul>
<h2 style="margin-bottom: 1.em; margin-top: 2.5em;"><a id="BATCHOPTIONS" name="BATCHOPTIONS"></a>How to Submit a Batch Job</h2>
<p>Non-interactive batch jobs are submitted with the <a href="http://scv.bu.edu/scc_manpages/qsub.txt"><strong>qsub</strong></a> command. The general form of the command is:</p>
<pre class="code-block"><code><span class="prompt">scc % </span><span class="command">qsub <span class="placeholder">[options] command [arguments]</span></span></code></pre>
<p>For example, to submit the <code><span class="command">printenv</span></code> command to the batch system, execute:</p>
<pre class="code-block"><code><span class="prompt">scc % </span><span class="command">qsub</span> -b y printenv
<span class="output">Your job <span class="placeholder">#jobID</span> ("printenv") has been submitted</span></code></pre>
<p>The option <code>-b y</code> tells the batch system that the following command is a binary executable. The output message of the <code><span class="command">qsub</span></code> command will print the job ID, which you can use to <a href="../tracking-jobs">monitor the job’s status</a> within the queue. While the job is running the batch system creates <em>stdout</em> and <em>stderr</em> files, which by default are created in the job’s working directory. These files are named after the job’s name with the extension ending in the job’s number, for the above example <code>printenv.o<span class="placeholder">#jobID</span></code> and <code>printenv.e<span class="placeholder">#jobID</span></code>. The first one will contain the output of the command and the second will have the list of warnings and&nbsp; errors, if any, that occurred while the job was running.</p>
<p>When running a program that requires arguments and passes additional directives to the batch system, it becomes useful to save them in a script file and submit this script as an argument to the <code><span class="command">qsub</span></code> command. For example, the following script <code>script.sh</code> will execute a simple python job:</p>
<pre class="code-block"><code>#!/bin/bash -l
 
<span class="comment"># program name or command and its options and arguments</span>
python myscript.py
</code></pre>
<div class="highlight-yellow"><b>Note:</b> To be processed correctly, the script must contain a blank line at the end of the file.</div>
<p>To submit this <code>script.sh</code> file to the batch system, execute:</p>
<pre class="code-block"><code><span class="prompt">scc % </span><span class="command">qsub</span> script.sh
<span class="output">Your job <span class="placeholder">#jobID</span> ("script.sh") has been submitted</span></code></pre>
<p>For other batch script examples, please see <a href="https://www.bu.edu/tech/support/research/system-usage/running-jobs/batch-script-examples/">Batch Script Examples</a>.</p>
<h2 style="margin-bottom: 1.em; margin-top: 2.5em;"><a id="MODULE" name="Module"></a>Software Versions and the Module Command</h2>
<p>To access software packages on the SCC you need to use a <code><span class="command">module</span></code> command. For example, even though there is a systems version of Python, it is very old and does not contain any popular packages. To get access to newer versions of the software, please use <a href="https://www.bu.edu/tech/support/research/software-and-programming/software-and-applications/modules/">Modules</a>. When a <code><span class="command">module</span></code> command is used in a bash script, the first line of the script must contain the “<code><span class="command">-l</span></code>” option to ensure proper handling of the module command:</p>
<pre class="code-block"><code>#!/bin/bash -l
 
<span class="comment"># Specify the version of MATLAB to be used</span>
module load matlab/2021b

<span class="comment"># program name or command and its options and arguments</span>
matlab -nodisplay -nodesktop -singleCompThread -batch "n=4, rand; exit"</code></pre>
<h2 style="margin-bottom: 1.em; margin-top: 2.5em;"><a name="job-options"></a>General Job Submission Directives</h2>
<p>There are a number of directives (options) that the user can pass to the batch system. These directives can either be provided as arguments to the <code><span class="command">qsub</span></code> command or embedded in the job script. In a script file the lines containing these directives begin with the symbols <code><b>#$</b></code> – here is an example:</p>
<pre class="code-block"><code>#!/bin/bash -l

<span class="command">#$</span> -P myproject       <span class="comment"># Specify the SCC project name you want to use</span>
<span class="command">#$</span> -l h_rt=12:00:00   <span class="comment"># Specify the hard time limit for the job</span>
<span class="command">#$</span> -N myjob           <span class="comment"># Give job a name</span>
<span class="command">#$</span> -j y               <span class="comment"># Merge the error and output streams into a single file
</span>

module load python3/3.8.10
python myscript.py
</code></pre>
<p>Below is the list of some of the most commonly used directives:</p>
<table>
<tbody>
<tr>
<td colspan="2" style="padding: 7px; background-color: #2c6696; color: #ffffff; text-align: center; font-size: 120%;">General Directives</td>
</tr>
<tr>
<th style="background-color: #c9d5d7; text-align: center; box-shadow: none; border: 1px solid #97a1a4;" width="20%">Directive</th>
<th style="background-color: #c9d5d7; text-align: center; box-shadow: none; border: 1px solid #97a1a4;" width="80%">Description</th>
</tr>
</tbody>
<tbody>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-l h_rt</b>=<em>hh:mm:ss</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Hard run time limit in <code><span class="placeholder">hh:mm:ss</span></code> format. The default is 12 hours.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-P</b> <em>project_name</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Project to which this jobs is to be assigned. This directive is <b>mandatory</b> for all users associated with any Med.Campus project.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-N</b> <em>job_name</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Specifies the job name. The default is the script or command name.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-o</b> <em>outputfile</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">File name for the stdout output of the job.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-e</b> <em>errfile</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">File name for the stderr output of the job.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-j y</b></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Merge the error and output stream files into a single file.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-m</b> <em>b|e|a|s|n</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Controls when the batch system sends email to you. The possible values are – when the job begins (b), ends (e), is aborted (a), is suspended (s), or never (n) – default.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-M</b> <em>user_email</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Overwrites the default email address used to send the job report.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-V</b></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">All current environment variables should be exported to the batch job.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-v</b> <em>env=value</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Set the runtime environment variable <code><span class="placeholder">env</span></code> to <code><span class="placeholder">value</span></code>.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-hold_jid</b> <em>job_list</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Setup job dependency list. <code><span class="placeholder">job_list</span></code> is a comma separated list of job ids and/or job names which must complete before this job can run. See <a href="https://www.bu.edu/tech/support/research/system-usage/running-jobs/advanced-batch/">Advanced Batch System Usage</a> for more information.</td>
</tr>
</tbody>
</table>
<h2 style="margin-bottom: 1.em; margin-top: 2.5em;"><a name="job-resources"></a>Resource Usage and Limits</h2>
<p>The Sun Grid Engine (SGE) allows a job to request specific <a href="https://www.bu.edu/tech/support/research/system-usage/running-jobs/resources-jobs/">SCC resources</a> necessary for a successful run, including a node with large memory, multiple CPUs, a specific queue, or a node with a specific architecture. The <a href="https://www.bu.edu/tech/support/research/computing-resources/tech-summary/">Technical Summary</a> contains hardware configuration for all SCC nodes. The <a href="https://www.bu.edu/tech/support/research/system-usage/running-jobs/advanced-batch/">Advanced Batch System Usage</a> page contains examples of running jobs which require parallel environments (OMP, MPI, GPU).</p>
<p>The following table lists the most commonly used options to request resources available on the SCC:</p>
<table>
<tbody>
<tr>
<td colspan="2" style="padding: 7px; background-color: #2c6696; color: #ffffff; text-align: center; font-size: 120%;">Directives to request SCC resources</td>
</tr>
<tr>
<th style="background-color: #c9d5d7; text-align: center; box-shadow: none; border: 1px solid #97a1a4;" width="30%">Directive</th>
<th style="background-color: #c9d5d7; text-align: center; box-shadow: none; border: 1px solid #97a1a4;" width="70%">Description</th>
</tr>
</tbody>
<tbody>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-l h_rt</b>=<em>hh:mm:ss</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Hard run time limit in <code><span class="placeholder">hh:mm:ss</span></code> format. The default is 12 hours.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-l mem_per_core</b>=<em>#G</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Request a node that has at least this amount of memory per core. Recommended choices are: 3G, 4G, 6G, 8G, 12G, 16G, 18G and 28G</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-pe omp</b> <em>N</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Request multiple slots for Shared Memory applications (OpenMP, pthread). This option can also be used to reserve a larger amount of memory for the application. <code><span class="placeholder">N</span></code> can vary. Currently, to request multiple cores on SCC’s shared nodes, we recommend selecting 1-4, 8, 16, 28, or 36 cores.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-pe mpi_#_tasks_per_node</b> <em>N</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Select multiple nodes for an MPI job. Number of tasks can be 4, 8, 12, 16, or 28 and <code><span class="placeholder">N</span></code> must be a multiple of this value. See <a href="https://www.bu.edu/tech/support/research/system-usage/running-jobs/parallel-batch/">Running Parallel Batch Jobs</a> for more information.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-t </b> <em>N</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Submit an Array Job with <code><span class="placeholder">N</span></code> tasks. N can be up to 75,000. For more information see <a href="https://www.bu.edu/tech/support/research/system-usage/running-jobs/advanced-batch/#array">Array Jobs</a></td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-l cpu_arch</b>=<em>ARCH</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Select a processor architecture (broadwell, ivybridge, cascadelake…). See <a href="https://www.bu.edu/tech/support/research/computing-resources/tech-summary/">Technical Summary</a> for all available choices.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-l cpu_type</b>=<em>TYPE</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Select a processor type (X5670, X5675, Gold-6132 etc.) See <a href="https://www.bu.edu/tech/support/research/computing-resources/tech-summary/">Technical Summary</a> for all available choices.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-l gpus</b>=<em>G</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Requests a node with GPUs. <em>G </em>is the number of GPUs. See <a href="https://www.bu.edu/tech/support/research/software-and-programming/programming/multiprocessor/gpu-computing/">GPU Computing</a> for more information.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-l gpu_type</b>=<em>GPUMODEL</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">To see the current list of available GPU models, run <code><span class="placeholder">qgpus</span></code> command. See <a href="https://www.bu.edu/tech/support/research/software-and-programming/programming/multiprocessor/gpu-computing/">GPU Computing</a> for more information.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-l gpu_c</b>=<em>CAPABILITY</em></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Specify minimum GPU capability. Current choices for <code><span class="placeholder">CAPABILITY</span></code> are 3.5, 5.0, 6.0, 7.0, and 8.6</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-l gpu_memory</b>=#G</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Request a node with a GPU that has 12G, 16G, 24G, 32G, or 48G of memory.</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;"><b>-l avx</b></td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Request a node that supports AVX and newer <a href="https://www.bu.edu/tech/support/research/software-and-programming/programming/compilers/cpu-architectures/">CPU instructions</a>. A small number of modules require support for these instructions.</td>
</tr>
</tbody>
</table>
<p>The following table summarizes the wall-clock runtime limits for different jobs based on their type:</p>
<table width="300">
<tbody>
<tr>
<td colspan="2" style="padding: 7px; background-color: #2c6696; color: #ffffff; text-align: center; font-size: 120%;">Run time lmits for shared nodes</td>
</tr>
<tr>
<th style="background-color: #c9d5d7; text-align: center; box-shadow: none; border: 1px solid #97a1a4;" width="30%">Type of the job</th>
<th style="background-color: #c9d5d7; text-align: center; box-shadow: none; border: 1px solid #97a1a4;" width="70%">Time limit on shared nodes</th>
</tr>
</tbody>
<tbody>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;">Single processor job</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">720 hours (30 days)</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;">OMP</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">720 hours (30 days)</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;">MPI</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">120 hours (5 days)</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;">GPU</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">48 hours (2 days)</td>
</tr>
</tbody>
</table>
<h2 style="margin-bottom: 1.em; margin-top: 2.5em;"><a id="ENV" name="ENV"></a>SGE Environment Variables</h2>
<p>When the job is scheduled to run, a number of environment variables are set and may be used by the program:</p>
<table width="300">
<tbody>
<tr>
<td colspan="2" style="padding: 7px; background-color: #2c6696; color: #ffffff; text-align: center; font-size: 120%;">Batch System Environment</td>
</tr>
<tr>
<th style="background-color: #c9d5d7; text-align: center; box-shadow: none; border: 1px solid #97a1a4;" width="30%">Environment Variable</th>
<th style="background-color: #c9d5d7; text-align: center; box-shadow: none; border: 1px solid #97a1a4;" width="70%">Description</th>
</tr>
</tbody>
<tbody>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;">JOB_ID</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Current job ID</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;">JOB_NAME</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Current job name</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;">NSLOTS</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">The number of slots requested by a job</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;">HOSTNAME</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Name of execution host</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;">SGE_TASK_ID</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">Array Job task index number</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;">SGE_TASK_STEPSIZE</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">The step size of the array job specification</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;">SGE_TASK_FIRST</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">The index number of the first array job task</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;">SGE_TASK_LAST</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">The index number of the last array job task</td>
</tr>
<tr>
<td style="padding: 7px; background-color: #ecf4f7; text-align: left; border: 1px solid #97a1a4;">TMPDIR</td>
<td style="padding: 7px; background-color: #ffffff; text-align: left; border: 1px solid #97a1a4;">The absolute path to the job’s temporary working directory</td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
							
														
						</div>
					</section>
				</div>















OUTPUT:

1. **Chunk Text:**
   ## How to Submit a Batch Job
   Non-interactive batch jobs are submitted with the [**qsub**](http://scv.bu.edu/scc_manpages/qsub.txt) command. The general form of the command is:
   ```
   scc % qsub [options] command [arguments]
   ```
   For example, to submit the `printenv` command to the batch system, execute:
   ```
   scc % qsub -b y printenv
   Your job #jobID ("printenv") has been submitted
   ```
   The option `-b y` tells the batch system that the following command is a binary executable. The output message of the `qsub` command will print the job ID, which you can use to [monitor the job’s status](../tracking-jobs) within the queue. While the job is running the batch system creates *stdout* and *stderr* files, which by default are created in the job’s working directory. These files are named after the job’s name with the extension ending in the job’s number, for the above example `printenv.o#jobID` and `printenv.e#jobID`. The first one will contain the output of the command and the second will have the list of warnings and errors, if any, that occurred while the job was running.
   When running a program that requires arguments and passes additional directives to the batch system, it becomes useful to save them in a script file and submit this script as an argument to the `qsub` command. For example, the following script `script.sh` will execute a simple python job:
   ```
   #!/bin/bash -l

   # program name or command and its options and arguments
   python myscript.py
   ```
   **Note:** To be processed correctly, the script must contain a blank line at the end of the file.
   To submit this `script.sh` file to the batch system, execute:
   ```
   scc % qsub script.sh
   Your job #jobID ("script.sh") has been submitted
   ```
   For other batch script examples, please see [Batch Script Examples](https://www.bu.edu/tech/support/research/system-usage/running-jobs/batch-script-examples/).

   **Tags:** batch job, qsub command, job submission, script execution  
   **Citation:** [Source URL](https://www.bu.edu/tech/support/research/system-usage/running-jobs/)  

2. **Chunk Text:**
   ## Software Versions and the Module Command
   To access software packages on the SCC you need to use a `module` command. For example, even though there is a systems version of Python, it is very old and does not contain any popular packages. To get access to newer versions of the software, please use [Modules](https://www.bu.edu/tech/support/research/software-and-programming/software-and-applications/modules/). When a `module` command is used in a bash script, the first line of the script must contain the “`-l`” option to ensure proper handling of the module command:
   ```
   #!/bin/bash -l

   # Specify the version of MATLAB to be used
   module load matlab/2021b

   # program name or command and its options and arguments
   matlab -nodisplay -nodesktop -singleCompThread -batch "n=4, rand; exit"
   ```

   **Tags:** software modules, module command, SCC software  
   **Citation:** [Source URL](https://www.bu.edu/tech/support/research/system-usage/running-jobs/)  

3. **Chunk Text:**
   ## General Job Submission Directives
   There are a number of directives (options) that the user can pass to the batch system. These directives can either be provided as arguments to the `qsub` command or embedded in the job script. In a script file the lines containing these directives begin with the symbols `#$` – here is an example:
   ```
   #!/bin/bash -l

   #$ -P myproject       # Specify the SCC project name you want to use
   #$ -l h_rt=12:00:00   # Specify the hard time limit for the job
   #$ -N myjob           # Give job a name
   #$ -j y               # Merge the error and output streams into a single file

   module load python3/3.8.10
   python myscript.py
   ```
   Below is the list of some of the most commonly used directives:
   
   | Directive                 | Description                                                                                      |
   |---------------------------|--------------------------------------------------------------------------------------------------|
   | **-l h_rt=hh:mm:ss**     | Hard run time limit in `hh:mm:ss` format. The default is 12 hours.                            |
   | **-P project_name**       | Project to which this job is to be assigned. This directive is **mandatory** for all users associated with any Med.Campus project. |
   | **-N job_name**           | Specifies the job name. The default is the script or command name.                             |
   | **-o outputfile**         | File name for the stdout output of the job.                                                    |
   | **-e errfile**            | File name for the stderr output of the job.                                                    |
   | **-j y**                  | Merge the error and output stream files into a single file.                                    |
   | **-m b|e|a|s|n**         | Controls when the batch system sends email to you. The possible values are – when the job begins (b), ends (e), is aborted (a), is suspended (s), or never (n) – default. |
   | **-M user_email**         | Overwrites the default email address used to send the job report.                              |
   | **-V**                    | All current environment variables should be exported to the batch job.                         |
   | **-v env=value**          | Set the runtime environment variable `env` to `value`.                                          |

   **Tags:** job submission directives, qsub options, scripting  
   **Citation:** [Source URL](https://www.bu.edu/tech/support/research/system-usage/running-jobs/)  

4. **Chunk Text:**
   ## Resource Usage and Limits
   The Sun Grid Engine (SGE) allows a job to request specific [SCC resources](https://www.bu.edu/tech/support/research/system-usage/running-jobs/resources-jobs/) necessary for a successful run, including a node with large memory, multiple CPUs, a specific queue, or a node with a specific architecture. The [Technical Summary](https://www.bu.edu/tech/support/research/computing-resources/tech-summary/) contains hardware configuration for all SCC nodes. The [Advanced Batch System Usage](https://www.bu.edu/tech/support/research/system-usage/running-jobs/advanced-batch/) page contains examples of running jobs which require parallel environments (OMP, MPI, GPU).
   The following table lists the most commonly used options to request resources available on the SCC:
   
   | Directive                       | Description                                                                                                      |
   |---------------------------------|------------------------------------------------------------------------------------------------------------------|
   | **-l h_rt=hh:mm:ss**           | Hard run time limit in `hh:mm:ss` format. The default is 12 hours.                                            |
   | **-l mem_per_core=#G**         | Request a node that has at least this amount of memory per core. Recommended choices are: 3G, 4G, 6G, 8G, 12G, 16G, 18G and 28G |
   | **-pe omp N**                  | Request multiple slots for Shared Memory applications (OpenMP, pthread). This option can also be used to reserve a larger amount of memory for the application. `N` can vary. Currently, to request multiple cores on SCC’s shared nodes, we recommend selecting 1-4, 8, 16, 28, or 36 cores. |
   | **-pe mpi_#_tasks_per_node N** | Select multiple nodes for an MPI job. Number of tasks can be 4, 8, 12, 16, or 28 and `N` must be a multiple of this value. See [Running Parallel Batch Jobs](https://www.bu.edu/tech/support/research/system-usage/running-jobs/parallel-batch/) for more information. |
   | **-t N**                        | Submit an Array Job with `N` tasks. N can be up to 75,000. For more information see [Array Jobs](https://www.bu.edu/tech/support/research/system-usage/running-jobs/advanced-batch/#array) |
   | **-l cpu_arch=ARCH**           | Select a processor architecture (broadwell, ivybridge, cascadelake…). See [Technical Summary](https://www.bu.edu/tech/support/research/computing-resources/tech-summary/) for all available choices. |
   | **-l cpu_type=TYPE**           | Select a processor type (X5670, X5675, Gold-6132 etc.) See [Technical Summary](https://www.bu.edu/tech/support/research/computing-resources/tech-summary/) for all available choices. |
   | **-l gpus=G**                  | Requests a node with GPUs. `G` is the number of GPUs. See [GPU Computing](https://www.bu.edu/tech/support/research/software-and-programming/programming/multiprocessor/gpu-computing/) for more information. |
   | **-l gpu_type=GPUMODEL**       | To see the current list of available GPU models, run `qgpus` command. See [GPU Computing](https://www.bu.edu/tech/support/research/software-and-programming/programming/multiprocessor/gpu-computing/) for more information. |
   | **-l gpu_c=CAPABILITY**        | Specify minimum GPU capability. Current choices for `CAPABILITY` are 3.5, 5.0, 6.0, 7.0, and 8.6 |
   | **-l gpu_memory=#G**           | Request a node with a GPU that has 12G, 16G, 24G, 32G, or 48G of memory.                        |
   | **-l avx**                     | Request a node that supports AVX and newer [CPU instructions](https://www.bu.edu/tech/support/research/software-and-programming/programming/compilers/cpu-architectures/). A small number of modules require support for these instructions. |

   The following table summarizes the wall-clock runtime limits for different jobs based on their type:
   
   | Type of the job               | Time limit on shared nodes |
   |-------------------------------|----------------------------|
   | Single processor job          | 720 hours (30 days)       |
   | OMP                           | 720 hours (30 days)       |
   | MPI                           | 120 hours (5 days)        |
   | GPU                           | 48 hours (2 days)         |

   **Tags:** resource limits, SCC resources, job type  
   **Citation:** [Source URL](https://www.bu.edu/tech/support/research/system-usage/running-jobs/)  

5. **Chunk Text:**
   ## SGE Environment Variables
   When the job is scheduled to run, a number of environment variables are set and may be used by the program:
   
   | Environment Variable         | Description                                          |
   |------------------------------|------------------------------------------------------|
   | JOB_ID                       | Current job ID                                       |
   | JOB_NAME                     | Current job name                                     |
   | NSLOTS                       | The number of slots requested by a job               |
   | HOSTNAME                     | Name of execution host                               |
   | SGE_TASK_ID                  | Array Job task index number                         |
   | SGE_TASK_STEPSIZE            | The step size of the array job specification         |
   | SGE_TASK_FIRST               | The index number of the first array job task         |
   | SGE_TASK_LAST                | The index number of the last array job task          |
   | TMPDIR                       | The absolute path to the job’s temporary working directory |

   **Tags:** SGE environment variables, job execution, batch system  
   **Citation:** [Source URL](https://www.bu.edu/tech/support/research/system-usage/running-jobs/)  